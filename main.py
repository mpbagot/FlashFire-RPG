#!/usr/bin/env python3

from random import *
import hashlib
import socket
import sys
import threading
from effects import *
from player import *
from world import *
from time import *

class Game:
    def __init__(self):
        # import pygame
        # pygame.init()
        # pygame.mixer.music.load('music/main.mp3')
        # pygame.mixer.music.play()
        print("=================")
        print("||FlashFire RPG||")
        print("=================")
        print('')
        play = input('Would you like to start a new game join a LAN server or load a previous save?[new/join/load] ')
        self.id = 0
        if play == "load":
            self.load(input('Save Game Filename: '))
        elif play == "join":
            addr, sock = self.join_server(inputf('Hostname of Host Server: '))
            if addr == "failed":
                printf('Critical Error! Exiting Game...')
                return
            self.run(addr, sock)
            return
        else:
            self.new()
        self.run()

    def load(self, file):
        '''
        Load pre-existing variables from a given file.
        '''
        print()
        try:
            with open(file+'.sv') as f:
                lines = f.read().split('\n')
                for line in lines:
                    if line.startswith('player'):
                        line = line[7:]
                        printf('Loading Player...')
                        # Create a player object from the string
                        self.player = Player.get_by_string(line)
                    elif line.startswith('inv'):
                        printf('Loading Inventory...')
                        line = line.split('|')[1:]
                        # Fill the player's inventory
                        self.player.inventory.contents = eval(line[0])
                    elif line.startswith('world'):
                        print()
                        printf('Loading World...')
                        line = line.split('|')[1:]
                        # Generate a world from the file, Takes a while.
                        self.world = World.generate_from_file(eval(line[0]), pos=self.player.pos)
            printf('\nGame Load Complete!\n')
        except FileNotFoundError:
            printf('Save File Not Found! Defaulting to New Game.')
            self.new()

    def new(self):
        '''
        Randomly generate new variables for a game
        '''
        #Ask for difficulty, used for world gen
        print()
        diff = inputf("Difficulty[easy/medium/hard]: ")
        print()
        #Default to medium if entry is invalid
        diff = "medium" if diff not in ('easy', 'medium', 'hard') else diff

        #generate a randomised starting area for the player
        pos = [randint(0, 999), randint(0, 999)]

        ##Create a Player randomly based on name
        while 1:
            name = inputf("What is your Character's name? ")
            if inputf("'{}', Are you sure this name is correct[Y/N]? ".format(name)) == "Y":
                break
        print()
        printf('Generating World...')
        #generate a world
        self.world = World(1000, 1000, diff, 2, pos)
        print()
        printf('Generating Character...')
        #Generate a SHA256 hash of the name.
        m = hashlib.sha256()
        m.update(name.encode())
        seed = m.hexdigest()

        #Convert the hex hash to an int (64 chars long!!)
        seed = genSeed(seed)

        #And create a Player object with it and the name
        self.player = Player(seed, name, pos)
        printf("Character Generation Complete!")
        print()
        sleep(1)

    def join_server(self, addr):
        '''
        Join a given server and convert the game to a dedicated Client
        '''

        name = inputf("Character Name: ")
        print()
        # Generate the hash of the char name for player gen
        m = hashlib.sha256()
        m.update(name.encode())
        seed = m.hexdigest()

        #Convert the hex hash to an int (64 chars long!!)
        seed = genSeed(seed)
        #set the client-side player
        self.player = Player(seed, name, [randint(0, 999) for a in range(2)])
        print()
        printf('Connecting to server...')
        # Initialise the socket
        sock = socket.socket()
        addr = (addr, 6657)
        try:
            # Attempt to connect to the given server
            sock.connect(addr)
            # Send the join signal to the server
            sock.sendall(('join|'+self.player.get_save_string()+"|"+str(self.player.inventory.contents)).encode())
            self.id = int(sock.recv(128).decode())
            return (addr, sock)
        except socket.gaierror:
            # Error if the server is not running or unable to be connected to
            printf('Error! Server not found!')
            return ('failed', '12345')

    def run(self, adr="", conn=""):
        '''
        Run a Client-side or Singleplayer game
        '''
        id = self.id
        printf('Starting Game.')
        sleep(1)

        #Clear the screen before starting
        for a in range(50):
            print('')

        x = True

        #Main game loop, break out to exit game
        while True:
            try:
                # Check if description should be printed
                if x:
                    # Check if running singleplayer or client game
                    if not adr:
                        # generate a description if running singleplayer
                        printf(self.world.get_description(self.player.pos))
                    else:
                        # Fetch description from server if running as client
                        conn.sendall('getdesc'.encode())
                        d = conn.recv(4096).decode()
                        printf(str(d))

                # Ask for a command
                comm = input('Command >>> ')

                if adr:
                    # send commands to server instead
                    x = self.run_lan_com(comm, conn)

                else:
                    # Run commands on local machine if playing singleplayer
                    x = self.run_command(comm)

            except KeyboardInterrupt:
                # prompt to exit when Ctrl+C is pressed
                opt = inputf('Continue or Exit?[cont/exit] ')
                if opt == 'exit':
                    if adr:
                        printf("Exiting...")
                    else:
                        printf('Saving and Exiting...')
                    break

            except BrokenPipeError:
                # Exit the game if the server is disconnected/quit
                print('Server Disconnected\nExiting Game...')
                return

        if adr:
            #Close the socket if we are connected over lan
            conn.close()
        else:
            #Save the game immediately before exiting
            self.save()

    def save(self):
        '''
        Save the current Singleplayer game to a file
        '''
        # Generate the save file
        towrite = ['player|'+self.player.get_save_string(),
                   'inv|'+str(self.player.inventory.contents),
                   'world|'+self.world.get_save_string()]
        with open('save_default.sv', 'w') as f:
            # Write the plain-text to a file
            f.write('\n'.join(towrite))

    def run_lan_com(self, comm, conn):
        '''
        Transmit a command to a server and recieve result
        '''

        if comm.startswith('talk to '):
            # Start a dialogue scenario on the server
            conn.send(('talk|begin_conv_'+comm.split()[-1]).encode())
            result = conn.recv(65536).decode().split("|")
            # Loop the conversation back and forth and print, here on the client-side
            while result[-2].split()[-1] not in ('Goodbye.', 'Farewell!'):
                printf(result[-2])
                conn.send(('talk|'+input(self.player.name+': ')).encode())
                result = conn.recv(65536).decode().split("|")
        elif comm == 'inventory':
            conn.send('inventory'.encode())
            conn.send(inputf('|-Inv Command-> ').encode())
            result = conn.recv(1024).decode().split('|')
            while not result[-1] in ('exit', 'quit', 'done'):
                printf(result[-1])
                conn.send(inputf('|-Inv Command->').encode())
                result = conn.recv(1024).decode().split('|')
            hp_change = int(result[0])
            self.player.stats['health'] += hp_change
            if self.player.stats['health'] > self.player.stats['max_health']:
                self.player.stats['health'] = self.player.stats['max_health']
            return

        else:
            conn.send(("command|"+comm).encode())
            result = conn.recv(65536).decode().split("|")
        if result[0] == 'disconnect':
            raise KeyboardInterrupt
        if result[0] == 'up':
            # Update player variables if the server requires it
            r = result[1:-1]
            self.player.pos = eval(r[0])
            self.player.inventory.contents = eval(r[1])
            self.player.stats = eval(r[2])
        if comm not in ('show map'):
            printf(result[-2])
        else:
            print(result[-2])
        # Return either true or false to re-displaying description
        return bool(int(result[-1]))

    def run_command(self, comm):
        '''
        Run a given command on a Singleplayer world.
        '''
        comm = comm.lower()
        pos = self.player.pos
        node = self.world.get_node(pos[0], pos[1])
        print()
        #check for comm commands and run an action as a result
        if comm == "look around":
            return True

        elif comm == 'show status':
            printf('Status:\n{}\n\n{}'.format(str(self.player), str(self.player.inventory)))

        elif comm == 'inventory':
            self.player.stats['health'] += self.player.inventory.modify()
            if self.player.stats['health'] > self.player.stats['max_health']:
                self.player.stats['health'] = self.player.stats['max_health']

        elif comm == 'save':
            # Create a new thread and save with that
            printf('Saving...')
            t = threading.Thread(target=self.save)
            t.daemon = False
            t.start()
            sleep(0.5)

        elif comm == "exit":
            raise KeyboardInterrupt

        elif comm == "show map":
            # Generate a sub-array of the current area around the player
            array = [[self.world.get_node(pos[0]+a,pos[1]+b) for a in range(-3, 3) if pos[0] > -a and pos[0] < 999-a] for b in range(-2, 2) if pos[1] > -b and pos[1] < 999-b]
            map_art = []
            for i, row in enumerate(array):
                # Check for north/south passages and clear the two middle hashes
                if i != 0:
                    top = ''
                    # Loop each node and create a top for the square on the map
                    # to show if you can go north/south
                    for a in row:
                        top += '########' if not a.hasNorth else '###  ###'
                    # Add the row to the map_art
                    map_art.append(top)
                else:
                    # If it's the top row then just create a solid border
                    map_art.append('#'*8*len(row))
                for a in range(4):
                    line = ''
                    for m, node in enumerate(row):
                        r = '#      #'
                        if a in (1,2):
                            if a == 1:
                                # Generate the node name text and the walls on the map square (if applicable)
                                if m == 3 and i == 2:
                                    r = "{}you're{}".format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                                elif node.typ == 'grass_plains':
                                    r = '{}grass {}'.format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                                else:
                                    r = "{}{}{}".format("#" if not node.hasWest else ' ', (' '*((6-len(node.typ))//2))+node.typ+(' '*((6-len(node.typ))//2)), '#' if not node.hasEast else ' ')
                            elif a == 2:
                                # As above but with the second word of the node name if applicable
                                if m == 3 and i == 2:
                                    r = "{} here!{}".format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                                elif node.typ == 'grass_plains':
                                    r = '{}plains{}'.format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                                else:
                                    r = "{}      {}".format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                        # Add it to the line
                        line += r
                    # Add the line to the map_art
                    map_art.append(line)
            # Add a bottom border to the map_art
            map_art.append("#"*(8*len(row)))
            for a in map_art:
                # Print the map quickly
                print(a)

        elif comm.startswith('talk to'):
            dia = 0
            # Create a list to be able to check which error occurs later on
            g = [1,0]
            name = comm.split()[-1]
            name = name[0].upper() + name[1:]
            if name == 'Person':
                # If the player is just looking for a random person
                if len(node.npc) > 0:
                    # If any person is found nearby then create a dialogue with that person
                    dia = Dialogue(self.player, node, node.npc[random.randint(0, len(node.npc)-1)])

            else:
                # If the player is looking for a specific NPC
                for n in node.npc:
                    # Iterate through all NPC's nearby
                    if name == n.name:
                        # If the NPC has the right name then adjust the array
                        # and start a Dialogue with it
                        dia = Dialogue(self.player, node, n)
            if dia != 0:
                # If a dialogue was created then run it
                Game.run_dialogue(dia)
                print()
                return
            else:
                # If no dialogue was started then print an appropriate error
                printf('There\'s no-one here named that!' if name != "Person" else 'There\'s no-one here!')


        elif comm.startswith('go'):
            # find the chosen direction
            di = comm.split()[-1].lower()
            dc = {'north':[1, -1, node.hasNorth], 'south':[1, 1, node.hasSouth],
                  'east':[0, 1, node.hasEast], 'west':[0, -1, node.hasWest]}
            # Get travel data
            tup = dc.get(di)

            if tup and tup[2]:
                # Move in chosen direction if possible
                self.player.pos[tup[0]] += tup[1]
                printf('Moving {}...'.format(di[0].upper()+di[1:]))
                return True
            else:
                # Yell at player if there is no passageway
                printf('No passage!')

        else:
            # Yell at player if they input an invalid command
            printf('Invalid Command!')
        return False

    @staticmethod
    def run_dialogue(dial, over_lan=False):
        '''
        A static method to run a given dialogue object on a singleplayer world
        '''
        # Print the introducing statement
        printf(dial.start_talk())
        while not dial.is_finished():
            # Input and respond with the dialogue whilst the NPC keeps talking
            response = input(dial.p_name+': ')
            text = dial.respond(response)
            printf(text)

class MP_Game:
    def __init__(self):
        printf('Initialising Server...')
        printf("Server games cannot be saved, any items or progress you make will be deleted!")
        print()
        play = input('Would you like to start a new game or load a previous save?[new/load] ')
        if play == "load":
            self.load(input('Save Game Filename: '))
        else:
            self.new()
        self.run()

    def load(self, file):
        '''
        Load a singleplayer save file and host it as the server world
        '''
        print()
        try:
            self.players = []
            with open(file+'.sv') as f:
                lines = f.read().split('\n')
                for line in lines:
                    # Iterate through the save file until the world data is found
                    if line.startswith('world'):
                        # Generate a world object using the string
                        printf('Loading World...')
                        line = line.split('|')[1:]
                        self.world = World.generate_from_file(eval(line[0]))
            printf('\nGame Load Complete!\n')

        except FileNotFoundError:
            # Print an error and default to a new game if the input save file doesn't exist
            printf('Save File Not Found! Defaulting to New Game.')
            self.new()

    def new(self):
        '''
        Generate a new world for use on the server
        '''
        #Ask for difficulty, used for world gen
        print()
        diff = inputf("Difficulty[easy/medium/hard]: ")
        #Default to medium if entry is invalid
        diff = "medium" if diff not in ('easy', 'medium', 'hard') else diff

        #generate an empty world
        self.world = World(1000, 1000, diff, 2)
        print()
        self.players = []
        sleep(1.5)

    def handle_user(self, conn, addr):
        '''
        A thread-only function used to control communication with clients
        '''
        while True:
            try:
                data = conn.recv(1024).decode()
            except ConnectionResetError:
                printf('Player {} has exited the game!'.format(p.name))
            if data == "getdesc":
                # Return the area description
                string = self.world.get_description(p.pos)
                # Loop through the player list to determine if any other players are nearby
                for player in self.players:
                    # If the player is here and not the current player then tell the current player about them
                    if player.name != p.name and player.pos == p.pos:
                        string += '\nPlayer {} is nearby!'.format(p.name)
                # send the byte-encoded string to the client
                conn.sendall(string.encode())

            elif data.startswith('join'):
                # Generate the joining user's user object
                line = data[5:]
                p = Player.get_by_string(line)
                p.inventory.contents = eval(line.split('|')[-1])
                # Print a nice message
                printf('Player {} has joined the server!'.format(p.name))
                # Add the user object to the players list
                self.players.append(p)
                self.world.s_chunk = [(p.pos[0]//10)-1, (p.pos[1]//10)-1]
                # Make a new thread and generate a small area around the joining player in it
                t = threading.Thread(target=self.world.generate_start, args=(self.world.diff, self.world.lod))
                t.daemon = True
                t.start()
                index = self.players.index(p)
                # Return the player's unique index to them
                conn.sendall(str(index).encode())
            elif data == "disconnect":
                break
            elif data.startswith('command'):
                # Pull the command from the recieved message
                comm = data.split('|')[-1]
                # Reply with the correct response to the client
                conn.send(self.run_command(comm, index).encode())
                # Print that the player is leaving the game if they type exit
                if comm == "exit":
                    printf('Player {} has exited the game!'.format(p.name))
            elif data.startswith('inventory'):
                self.players[index].inventory.modify(True, conn)

            # Handle dialogue over the lan communication.
            elif data.startswith('talk'):
                comm = data.split('|')[-1]
                if comm.startswith('begin_conv_'):
                    # Start the dialogue if the conversation is just beginning
                    name = comm.split('_')[-1]
                    name = name[0].upper() + name[1:]
                    node = self.world.get_node(p.pos[0], p.pos[1])
                    dia = ''
                    # If a random person was requested then pick a random person in the area
                    if name == 'Person':
                        if len(node.npc) > 0:
                            n = node.npc[random.randint(0, len(node.npc)-1)]
                            dia = Dialogue(p, node, n)
                    # If a name was selected then find if that person is in the area and begin dialogue
                    else:
                        for n in node.npc:
                            if n.name == name:
                                dia = Dialogue(p, node, n)
                        if not dia:
                            # If no NPC's were found then check the players
                            for player in self.players:
                                if player != p and player.pos == p.pos and player.name.lower() == name.lower():
                                    # Set the players as in conversation so they wont be interrupted.
                                    self.players[self.players.index(player)].in_conversation = True
                                    self.players[index].in_conversation = True
                                    while True:
                                        # TODO Loop and have conversation somehow
                                        # HOW DO I DO THIS!?!?!?!
                                        pass
                    # If the suggested NPC is nearby then begin the talk
                    if dia:
                        text = dia.start_talk()
                    # Otherwise print out that that person is not nearby.
                    else:
                        text = 'That person is not nearby!'
                # If the dialogue is being continued then just return a response
                elif dia:
                    text = dia.respond(comm)
                # If the dialogue AI says goodbye then just quit
                if text.endswith('Farewell!') or text.endswith('Goodbye.'):
                    node.npc[node.npc.index(n)].known_players += p.name
                # Return the encoded response to the client to be printed
                conn.send('{}|0'.format(text).encode())
        conn.close()

    def run(self):
        '''
        Listen for connecting clients and create a new client handler thread.
        Allows for up to 5 clients to join.
        '''
        printf('Starting Game.')
        try:
            # Open the socket
            server = socket.socket()
            hostname = socket.gethostname()
            port = 6657
            # Bind the hostname and port data to the opened socket
            server.bind((hostname, port))

        except Exception as e:
            print(e)
            # Error if something fails
            printf('Server Hosting Failed!')
            printf('Exiting Server.')
            return

        printf('Server Hosting successful!\n')

        # Try to get the ip address, return None if it couldn't be retreived
        ip = get_ip()

        if ip is None:
            # Tell the user that the IP Address couldn't be found
            printf('IP Address Unobtainable! Please use ipconfig or ifconfig to find this computer\'s IPv4 address')
        else:
            # Print out the IP Address for clients to connect to
            printf('IP Address of server is: '+str(ip))
        printf('Press Ctrl+C to exit at any time.\n')
        try:
            # Listen for connecting clients
            server.listen(5)
            while True:
                # Accept the connection
                conn, addr = server.accept()
                # Run a client handler on a new thread
                t = threading.Thread(target=self.handle_user, args=(conn, addr))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            # Exit upon pressing Ctrl+C
            printf('Exiting...')

    def run_command(self, comm, id):
        '''
        Run a given command on the server and pass back anything to the client
        '''
        pos = self.players[id].pos
        node = self.world.get_node(self.players[id].pos[0], self.players[id].pos[1])
        text = ''
        up = ''
        #check for comm commands and run an action as a result
        if comm == "look around":
            return text+'|1'

        elif comm == 'show status':
            text = '\nStatus:\n{}\n\n{}'.format(str(self.players[id]), str(self.players[id].inventory))

        elif comm == "exit":
            return 'disconnect'

        elif comm == "show map":
            # Get a small array of nodes immediately around the player
            array = [[self.world.get_node(pos[0]+a,pos[1]+b) for a in range(-3, 3) if pos[0] > -a and pos[0] < 999-a] for b in range(-2, 2) if pos[1] > -b and pos[1] < 999-b]
            map_art = []
            for i, row in enumerate(array):
                # check for north/south passages and clear the two middle hashes
                if i != 0:
                    # generate the top row to determine if the nodes have north/south travel openings
                    top = ''
                    for a in row:
                        top += '########' if not a.hasNorth else '###  ###'
                    map_art.append(top)
                else:
                    # If at the top of the map, then just make a solid line
                    map_art.append('#'*8*len(row))
                for a in range(4):
                    # Generate the middle of the node square
                    line = ''
                    for m, node in enumerate(row):
                        # Make an empty row with solid walls on either side
                        # (used for first and last of the middle rows)
                        r = '#      #'
                        if a == 1:
                            # Add the walls and node name words to the line
                            if m == 3 and i == 2:
                                r = "{}you're{}".format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                            elif node.typ == 'grass_plains':
                                r = '{}grass {}'.format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                            else:
                                r = "{}{}{}".format("#" if not node.hasWest else ' ', (' '*((6-len(node.typ))//2))+node.typ+(' '*((6-len(node.typ))//2)), '#' if not node.hasEast else ' ')
                        elif a == 2:
                            # Same as above but for the second line of the node name
                            if m == 3 and i == 2:
                                r = "{} here!{}".format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                            elif node.typ == 'grass_plains':
                                r = '{}plains{}'.format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')
                            else:
                                r = "{}      {}".format("#" if not node.hasWest else ' ', '#' if not node.hasEast else ' ')

                        # Add the node string to the overall line
                        line += r
                    # Add the line to the whole map_art array
                    map_art.append(line)
            # Add a closing bottom line
            map_art.append("#"*(8*len(row)))
            # Pass the entire array (joined with newlines) back to the client
            text = '\n'.join(map_art)

        elif comm.startswith('go'):
            # find the chosen direction
            di = comm.split()[-1].lower()
            dc = {'north':[1, -1, node.hasNorth], 'south':[1, 1, node.hasSouth],
                  'east':[0, 1, node.hasEast], 'west':[0, -1, node.hasWest]}
            # Get travel data
            tup = dc.get(di)

            if tup and tup[2]:
                # Move in chosen direction if possible
                self.players[id].pos[tup[0]] += tup[1]
                text += '\nMoving {}...'.format(di[0].upper()+di[1:])
                up = "up|{}|{}|{}".format(self.players[id].pos, self.players[id].inventory.contents, self.players[id].stats)
                return '{}|{}|1'.format(up, text)
            else:
                # Yell at player if there is no passageway
                text += '\nNo passage!'

        else:
            # Yell at player if they input an invalid command
            text += '\nInvalid Command!'
        return text+'|0'

##TODO in other file, make dialogue AI
##TODO in other file, make enemy AI

def get_ip():
    import socket
    # 1: Use the gethostname method
    ipaddr = socket.gethostbyname(socket.gethostname())
    # If the found IP Address is not a localhost IP then return it
    if not ipaddr.startswith('127'):
        return ipaddr

    # 3: Use OS specific command
    import subprocess, platform
    os_str=platform.system().upper()

    if os_str=='LINUX' :

        # Linux:
        arg='ip route list'
        # Run the above command on the Bash Shell
        p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
        data = p.communicate()
        # Pull the output back in
        sdata = data[0].decode().split()
        # print(sdata)
        try:
            # Find the IP Address if there
            ipaddr = sdata[ sdata.index('src')+1 ]
            return ipaddr

        except:
            return None

    elif os_str=='WINDOWS' :

        # Windows:
        arg='route print 0.0.0.0'
        # Run the above command on the Windows CMD shell
        p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
        data = p.communicate()
        # Pull the output back in
        strdata=data[0].decode()
        sdata = strdata.split()

        # Loop through/parse to find the IP Address
        while len(sdata)>0:
            if sdata.pop(0)=='Netmask' :
                if sdata[0]=='Gateway' and sdata[1]=='Interface' :
                    ipaddr=sdata[6]
                    break
    # Return a None object if nothing was found
    return None

g = Game() if input("Launch Server or Singleplayer[MP/SP]: ") != 'MP' else MP_Game()
