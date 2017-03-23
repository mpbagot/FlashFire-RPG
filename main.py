#!/usr/bin/env python3

from random import *
import hashlib
import socket
import sys
import threading
from effects import *
from player import *
from world import *
import math
from time import *

class Game:
    def __init__(self,title="Flashfire RPG"):
        print()
        # import pygame
        # pygame.init()
        # play_music('title_music')
        # Print the title in a nice box.
        print_title(title)
        play = input('Would you like to start a new game, join a LAN server\nor load a previous save?[new/join/load] ')
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
        self.player = Player(seed, name, pos, False if diff == 'hard' else True)
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

        if adr or not self.world.is_loading:
            play_intro('intro.txt')

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
                    # if the command doesn't require and server-client
                    # interaction, i.e the help command, then just run it client-side
                    if comm.lower() == 'help':
                        x = self.run_command('help')
                        continue

                    # otherwise send commands to server instead
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
        printf("Save Complete!")

    def run_lan_com(self, comm, conn):
        '''
        Transmit a command to a server and recieve result
        '''
        if comm.startswith('talk to '):
            # Start a dialogue scenario on the server
            conn.send(('talk|begin_conv_'+comm.split()[-1]).encode())
            result = conn.recv(65536).decode().split("|")
            # Loop the conversation back and forth and print, here on the client-side
            while result[-2].split()[-1].lower() not in ('goodbye', 'farewell'):
                printf(result[-2])
                conn.send(('talk|'+input(self.player.name+': ')).encode())
                result = conn.recv(65536).decode().split("|")

        elif comm.startswith('fight'):
            # Get the enemy's name or generic enemy
            en = comm.split()[-1]
            # Send the fight signal to the server to initiate combat
            conn.sendall(('fight|'+en).encode())
            result = conn.recv(4096).decode().split('XXX')
            result.append('')
            s = result[1]
            result = result[0]
            print(result)
            # recieve a success or fail signal and handle it
            if result.startswith("fail"):
                print(result.split('|')[1])
            else:
                if not s:
                    result = s+(conn.recv(4096).decode())
                else:
                    result = s
                while result[:3] not in ('dea', 'win','run'):
                    # While the server hasnt replied dead, win or run
                    if result.startswith('text'):
                        printf(result.split('|')[1])
                    if result.startswith('alert'):
                        printf(result.split('|')[1])
                        item = input('Choose an Item: ')
                        while not item.isnumeric() and item >= len(p.inventory.get_combat()):
                            item = input('Invalid Item ID!\nChoose an Item: ')
                        conn.sendall(str(item).encode())
                    action = ''
                    while not action:
                        # Grab the action command from the player
                        action = input('Action: ')
                    # send it to the server and get the result
                    conn.send(action.encode())
                    result = conn.recv(4096).decode()

                if result.startswith("win"):
                    # print an encouraging message
                    printf('You killed the {}!'.format(en))
                    gxp = result.split('|')[1]
                    # unpack the tuple into variables
                    g,xp,hp_change = eval(gxp)
                    g *= self.player.stats['level']
                    # Add the gained experience and gold
                    self.player.xp += xp
                    self.player.inventory.add('gold', g)
                    # Tell the player about it
                    printf('You found {} Gold!'.format(g))
                    printf('You gained {} XP!'.format(xp))
                    # Adjust the hp
                    self.player.stats['health'] += hp_change

                if result == "dead":
                    # Print message
                    print('You have died!!!')
                    sleep(3)
                    # Wait 3 seconds, clear the screen and reset the game.
                    # TODO fix the bug where restarting 1000 times without exiting will crash the game
                    print('\n'*50)
                    g = Game()
                    sys.exit()
                if result.startswith('run'):
                    # tell the player that they escaped
                        printf('You flee from battle. The {} does not follow.'.format(result.split('|')[1]))
                return False

        elif comm == 'inventory':
            conn.send('inventory'.encode())
            # Send the inventory command to the server
            conn.send(inputf('|-Inv Command-> ').encode())
            # recieve and parse the result.
            result = conn.recv(1024).decode().split('|')
            while not result[-1] in ('exit', 'quit', 'done'):
                # For as long as the client doesn't quit then repeat the above
                printf(result[-1])
                conn.send(inputf('|-Inv Command->').encode())
                result = conn.recv(1024).decode().split('|')
            hp_change = int(result[0])
            # add the hp change to the player.
            self.player.stats['health'] += hp_change
            if self.player.stats['health'] > self.player.stats['max_health']:
                self.player.stats['health'] = self.player.stats['max_health']
            return

        else:
            conn.send(("command|"+comm).encode())
            result = conn.recv(65536).decode().split("|")
            if comm == "enter store":
                if result[0] == "exit":
                    printf('There\'s no store here!')
                    return False
                while result[0] != 'Exiting the store...':
                    conn.send(input('>>> ').encode())
                    result = conn.recv(4096).decode().split('|')
                    printf(result[0])
                return False
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

        if comm.startswith("help"):
            if comm == "help":
                # if the player just asked 'help' then display general help
                text = ('''\nlook around - Display the area description again.
go <direction> - Move your character in the chosen direction (n/s/e/w)
inventory - Start the inventory screen. Allows you to drop, eat and equip items.
talk to <name>|person - Start a conversation with a person in the area.
show map - Display a simple ASCII art map.
show status - Display the player\'s current status and inventory.
fight enemy|<name> - Initiate combat with a nearby enemy or named enemy.
enter store - Enter a store if in a city area, allows for trade.
save - Save the game (Singleplayer only)
exit - Exit or disconnect from the game.

Use \'help inventory\' for help with the inventory,
or \'help trade\' for help with stores.
''')
            else:
                s = ''.join(comm.split()[1:])
                if s == "inventory":
                    # If they asked for help with the inventory then help them with that.
                    text = '''eat <item_id> - Eat a single item with item_id and restore some HP.
drop <item_id> <amount> - Drop an amount of items with item_id.
equip <item_id> <left|right|armour> - Equip the item with item_id in the given spot.
exit - Return to the game.'''
                elif s == "trade":
                    # ditto as above for trade
                    text = ''''''
                else:
                    # Or error if invalid option
                    text = ('Invalid help options!')
            # Lastly print and return
            printf(text)
            return False

        pos = self.player.pos
        node = self.world.get_node(pos[0], pos[1])
        print()
        #check for comm commands and run an action as a result
        if comm == "look around":
            return True

        elif comm == 'show status':
            printf('Status:\n{}\n\n{}'.format(str(self.player), self.player.get_stats()))

        elif comm == 'inventory':
            # Modify the player's health based on what they do in the inventory screen
            self.player.stats['health'] += self.player.inventory.modify()
            if self.player.stats['health'] > self.player.stats['max_health']:
                # If the players health goes above the max, then lower it back down.
                self.player.stats['health'] = self.player.stats['max_health']

        elif comm == 'enter store':
            if self.world.get_node(*self.player.pos).typ == "city":
                # Create a trade dialogue object
                trade = Trade(self.player, self.world.get_node(*self.player.pos))
                # Add the store to the area
                self.world.set_node(pos=self.player.pos, store=trade.store)
                # And run the trade dialogue
                trade.run_trade(self)
                return
            # Error if not in a city.
            printf('There\'s no store here!')

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
            array = [[0 for a in range(-3,3)] for b in range(-2,2)]
            for i, row in enumerate(array):
                for j, node in enumerate(row):
                    # If the area is an accessable spot, then add it to the map
                    if 999 >= pos[0]+(-3+j) >= 0 and 999 >= pos[1]+(-2+i) >= 0:
                        array[i][j] = self.world.get_node(pos[0]+(-3+j),pos[1]+(-2+i))
                    else:
                        # Otherwise create a null node area
                        array[i][j] = Null_Node()

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
                                    r = "{}{}{}".format("#" if not node.hasWest else ' ', (' '*((6-len(node.typ))//2))+node.typ+(' '*math.ceil((6-len(node.typ))/2)), '#' if not node.hasEast else ' ')
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

        elif comm.startswith('fight'):
            en = comm.split()[-1]

            node = self.world.get_node(self.player.pos[0], self.player.pos[1])
            en_len = len(node.enemies)
            enemy = False
            if en == "enemy":
                # the player is asking to fight a random entity
                if en_len > 0:
                    e = random.randint(0, en_len-1)
                    enemy = node.enemies[e]
                else:
                    # Return an error message if there are no enemies nearby
                    printf('There are no enemies nearby!')
                    return False
            else:
                # The player is asking to fight a named entity
                for a in node.enemies:
                    # Iterate through all enemies and check if any have the right name
                    if a.name == en:
                        e = node.enemies.index(a)
                        enemy = a
                if not enemy:
                    # Return an error message if there is no enemy with given name
                    printf('There is no enemy with that name!')
                    return False
            combat = Combat(self.player, enemy)
            init_hp = self.player.stats['health']
            gxp = combat.run()
            combat = None

            if gxp[0] == 'run':
                # If the player runs away
                return False

            if gxp == "dead":
                # Basically tell the player they died and restart the game
                # Because perma-death
                print('You have died!!!')
                sleep(3)
                # Wait 3 seconds, clear the screen and reset the game.
                # TODO fix the bug where restarting 1000 times without exiting will crash the game
                print('\n'*50)
                g = Game()
                sys.exit()
                return False

            # Modify the player variable due to changes during battle
            self.player = gxp[1]
            # Add one to the XP gained because of some glitch
            gxp = list(gxp)
            gxp[2] += 1

            # add the xp to the player
            printf('You gained {} XP!'.format(gxp[3]))
            printf('You found {} Gold!'.format(gxp[2]*self.player.stats['level']))
            self.player.xp += gxp[3]

            # Adjust level as neccessary
            self.player.stats['level'] = int(5**(len(str(self.player.xp))-2))

            # Add gold to the player's inventory
            self.player.inventory.add('gold', gxp[2]*self.player.stats['level'])

            x,y = self.player.pos
            # AND finally, remove the enemy that we just killed
            del self.world.chunk_array[y//10][x//10].array[y%10][x%10].enemies[e]

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
    def run_dialogue(dial):
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
        # Create an empty players array
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
                index = self.players.index(p)
                # Return the player's unique index to them
                conn.sendall(str(index).encode())
            elif data == "disconnect":
                break
            elif data.startswith('command'):
                # Pull the command from the recieved message
                comm = data.split('|')[-1]

                # Run a trader dialogue if you are trying to enter the store
                if comm == 'enter store':
                    if self.world.get_node(*p.pos).typ == "city":
                        # If we are in a city then create a new Trade dialogue
                        trade = Trade(p, self.world.get_node(*p.pos))
                        # Add the store to the area
                        self.world.set_node(pos=p.pos, store=trade.store)
                        # and initiate the trading system
                        trade.run_trade(self, conn, index)
                        conn.send('Exiting the store...'.encode())
                    else:
                        # Error if your not in a city.
                        conn.send('exit'.encode())

                else:
                    # Reply with the correct response to the client
                    conn.send(self.run_command(comm, index).encode())
                    # Print that the player is leaving the game if they type exit
                    if comm == "exit":
                        printf('Player {} has exited the game!'.format(p.name))

            elif data.startswith('inventory'):
                self.players[index].inventory.modify(True, conn)

            elif data.startswith('fight'):
                en = data.split('|')[-1]
                node = self.world.get_node(p.pos[0], p.pos[1])
                en_len = len(node.enemies)
                if en == "enemy":
                    # the player is asking to fight a random entity
                    if en_len > 0:
                        e = random.randint(0, en_len-1)
                        enemy = node.enemies[e]
                    else:
                        # Return an error message if there are no enemies nearby
                        conn.send('fail|There are no enemies nearby!'.encode())
                        continue
                else:
                    # The player is asking to fight a named entity
                    fail = 'fail'
                    for a in node.enemies:
                        # Iterate through all enemies and check if any have the right name
                        if a.name == en:
                            e = node.enemies.index(a)
                            enemy = a
                            fail = ''
                    if fail:
                        # If no nearby enemies have that name then check the players
                        for p in self.players:
                            if p.name == en:
                                enemy = p
                                fail = ''
                    if fail:
                        # Return an error message if there is no enemy with given name
                        conn.send('fail|There is no enemy with that name!'.encode())
                        continue
                combat = Combat(p, enemy)
                init_hp = p.stats['health']
                gxp = combat.run(conn)
                combat = None

                if gxp == None:
                    # If the player runs away
                    continue

                if gxp == "dead":
                    # Remove the player from the player list
                    # Death message is handled by client
                    del self.players[index]
                    return

                # Send the gold gain and xp gain to the client
                # so it can update it's local player details
                # also, send the hp change to the client
                hp_change = p.stats['health']-init_hp
                # Unpack the tuple, append the hp change, then repack
                gxp = list(gxp)
                gxp[1] += 1
                gxp.append(hp_change)
                gxp = tuple(gxp)
                # Send the tuple as a string to the client
                conn.send(('win|'+str(gxp[1:])).encode())

                # Modify the player variable due to changes during battle
                p = gxp[0]

                # add the xp to the player
                p.xp += gxp[2]

                # Adjust level as neccessary
                p.stats['level'] = int(5**(len(str(p.xp))-2))

                # Add gold to the player's inventory
                p.inventory.add('gold', gxp[1]*p.stats['level'])

                x,y = p.pos
                # AND finally, remove the enemy that we just killed
                del self.world.chunk_array[y//10][x//10].array[y%10][x%10].enemies[e]

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
            text = '\nStatus:\n{}\n\n{}'.format(str(self.players[id]), self.players[id].get_stats())

        elif comm == "exit":
            return 'disconnect'

        elif comm == "show map":
            # Get a small array of nodes immediately around the player
            array = [[0 for a in range(-3,3)] for b in range(-2,2)]
            for i, row in enumerate(array):
                for j, node in enumerate(row):
                    # If the area is an accessable spot, then add it to the map
                    if 999 >= pos[0]+(-3+j) >= 0 and 999 >= pos[1]+(-2+i) >= 0:
                        array[i][j] = self.world.get_node(pos[0]+(-3+j),pos[1]+(-2+i))
                    else:
                        # Otherwise create a null node area
                        array[i][j] = Null_Node()

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

##TODO in other file, make enemy AI

def print_title(string):
    '''
    Print the title you input in a nice box.
    '''
    print('='*80)
    blank = (70-len(string))//2
    print('||{}{}{}||'.format(blank*' '+'.::', string, '::.'+(blank+len(string)%2)*' '))
    print('='*80)
    print()

def get_ip():
    '''
    Try to the the Local IPv4 Address of this computer
    '''
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
