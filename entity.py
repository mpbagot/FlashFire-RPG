import random
from player import Player
from effects import *
from items import Item

class Enemy:
    def __init__(self, dif_ml, pos):
        self.pos = pos
        self.attack = random.randint(1,3)*dif_ml
        self.hp = random.randint(1, 10)*dif_ml
        # pull in the customisable name list from the other file
        names = [n for n in open('.enemy_names.txt').read().split('\n') if n != '']
        x = len(names)
        # and pick a random one from it
        self.name = names[random.randint(0, x-2)]
        if random.randint(0, 50) == 0:
            self.name = names[6]
        if self.name == 'Dragon':
            self.hp *= 2
            self.attack *= 1.5

    def __str__(self):
        '''
        Create the string to save entity data
        '''
        return '{}?{}?{}?{}'.format(str(self.pos), self.attack, self.hp, self.name)

    @staticmethod
    def get_by_string(string):
        '''
        Get an Enemy object by an input string
        '''
        string = string.split('?')
        e = Enemy(1, [0,0])
        #set object values from string
        e.pos = eval(string[0])
        e.attack = string[1]
        e.hp = string[2]
        e.name = string[3]
        return e

class NPC:
    def __init__(self, pos):
        self.pos = pos
        self.age = 18 + random.randint(0, 16)
        self.has_quest = random.randint(0, 3) == 0
        self.hp = random.randint(5, 10)
        self.known_players = []
        self.name, self.gender = open('names.txt').read().split('\n')[random.randint(0, 9)].split(',')

    def __str__(self):
        '''
        Create a string to save NPC data
        '''
        return '{}^{}^{}^{}^{}'.format(str(self.pos), self.hp, self.name, self.gender, str(self.known_players))

    @staticmethod
    def get_by_string(string):
        '''
        Evaluate a string and generate an NPC from it.
        '''
        string = string.split('^')
        npc = NPC(eval(string[0]))
        #set the npc values from the string
        npc.hp = int(string[1])
        npc.name = string[2]
        npc.gender = string[3]
        npc.known_players = eval(string[4])
        return npc

class Combat:
    def __init__(self, p, e):
        self.player = p
        e.hp *= ((p.stats['level']//10)+1)
        e.attack *= ((p.stats['level']//8)+1)
        self.enemy = e
        self.enemy.hp = int(self.enemy.hp)
        self.init_enem_hp = int(self.enemy.hp)

    def run(self, conn=None):
        '''
        Run the battle scenario, useable by client-server games or singleplayer.
        '''
        # Play the battle intro sound
        play_sound('fight_start')
        play_music('fight_music')

        if conn:
            # If playing as client, send success result to client
            conn.send('successXXX'.encode())
            print(self.enemy)
            if not isinstance(self.enemy, Player):
                # If the enemy is an enemy
                conn.sendall('text|\nA {} lurks nearby...\n\n(1) Attack\n(2) Items\n(3) Run\n'.format(self.enemy.name).encode())
            else:
                # Or if the enemy is another player
                conn.sendall('text|\n{} stands ready to fight!\n\n(1) Attack\n(2) Items\n(3) Run\n'.format(self.enemy.name).encode())
        else:
            # On singleplayer you can only fight enemies
            printf('\nA {} lurks nearby...\n\n(1) Attack\n(2) Items\n(3) Run\n'.format(self.enemy.name))

        noticed = False
        enem_dead = False

        self.enemy.hp = int(self.enemy.hp)

        while True:
            if conn:
                # If playing on lan, get the command from client
                comm = conn.recv(4096).decode()
            else:
                # Or just ask for input on singleplayer
                comm = input('Action: ')

            if comm == "1":
                weapon = self.player.inventory.equipped.get('right')
                if weapon:
                    dam = weapon.attrs.get('damage')
                else:
                    dam = 1
                if noticed and random.randint(0, 10) != 0:
                    dam += self.player.stats.get('attack')//25
                    text = "You strike at the {}. You deal {} damage.".format(self.enemy.name,dam)
                    self.enemy.hp -= dam
                elif not noticed:
                    if random.randint(0, 50) == 27:
                        # If you get a 2% chance then you suprise attack inst-kill the enemy
                        if conn:
                            conn.send(('Your surprise attack strikes the {}\'s weak spot.').encode())
                        enem_dead = True
                    elif random.randint(0, 20) == 7:
                        # Or if you get an unlucky 5% chance then the enemy dodges the attack
                        text = ('The {} reflexively dodges the attack at the last moment. Your attack misses entirely'.format(self.enemy.name))
                    else:
                        # Otherwise you get a critical for 2x damage
                        text = ('The {} wavers as you strike it unexpectedly.'.format(self.enemy.name))
                        self.enemy.hp -= dam*2
                else:
                    text = "You strike at the {}, but it moves too quickly and you miss.".format(self.enemy.name)
            elif comm == "2":
                if conn:
                    # If over lan then send an alert back to the client
                    conn.send('alert|{}'.format(self.player.inventory.get_combat()).encode())
                    item = int(conn.recv(3).decode())-1
                    if item == "exit":
                        continue
                    # Pull back the item id and grab the item tuple
                    item = self.player.inventory.get_combat().contents[item]
                else:
                    print(self.player.inventory.get_combat())
                    item = input('Choose an Item: ')
                    while True:
                        if not item:
                            # If they input nothing, error
                            print('No selection made!')
                        elif not item.isnumeric():
                            # IF they input a non-nubmber, error
                            if item == 'exit':
                                break
                            print('That\'s not an Item ID!')
                        elif int(item)-1 >= len(self.player.inventory.get_combat()) or int(item) < 1:
                            # If the ID they put in is out-of-bounds, error
                            print('Invalid Item ID!')
                        else:
                            # Otherwise, break and use that item ID
                            break
                        item = input('Choose an Item: ')
                    if item == 'exit':
                        continue
                    item = self.player.inventory.get_combat().contents[int(item)-1]
                # Get the item object for all operations below
                item = Item(*item)
                # Create the response message
                text = "You use a{} {}!".format('n' if item.attrs['name'][0].lower() in 'aeiou' else '', item.attrs['name'])

                if item.attrs.get('h_restore') > 0:
                    # If the item restores health
                    self.player.stats['health'] += item.attrs.get('h_restore')
                    # Add a helpful message
                    text += '\nYou gain {} HP!'.format(item.attrs.get('h_restore'))
                    if self.player.stats.get('health') > self.player.stats.get('max_health'):
                        # Add the health restoration for the item and round down to max health if it overflows
                        self.player.stats['health'] = self.player.stats.get('max_health')
                if item.attrs.get('damage') > 0:
                    # If the item is meant to do damage
                    self.enemy.hp -= item.attrs.get('damage')
                    # Add a helpful message
                    text += '\nThe {} loses {} HP!'.format(self.enemy.name, item.attrs.get('damage'))

                # TODO de-iterate the stack when you use the item

            elif comm == "3":
                # if you get really lucky then you can run
                if random.randint(0, abs(int((self.player.stats['speed']//10)+100-self.player.stats['level'])//10)) == 0 or not noticed:
                    if conn:
                        # If on a server, send a message to the client and exit
                        conn.send(('run|'+self.enemy.name).encode())
                        return
                    else:
                        # If on singleplayer just print a notice and exit
                        printf('You flee from battle. The {} does not follow.'.format(self.enemy.name))
                        return ('run',self.enemy.name)
                text = "The {} blocks your way out!".format(self.enemy.name)
            else:
                text = 'Invalid Option!'

            # Check if the player is dead
            if self.player.stats['health'] <= 0:
                if conn:
                    # Send the dead signal to the client
                    conn.send('dead'.encode())
                # and just return 'dead'
                return 'dead'

            # Check if enemy is dead
            if enem_dead or self.enemy.hp <= 0:
                if conn:
                    return (self.player, random.randint(1, 7)*self.player.stats['level'],random.randint(1, 3))
                else:
                    printf('You killed the {}!'.format(self.enemy.name))
                    return ('win', self.player, random.randint(1, 7)*self.player.stats['level'],random.randint(1, 3))

            # Let the enemy attack you
            if noticed and comm in ('1','2','3'):
                armour = self.player.inventory.equipped['armour']
                if armour:
                    dam_res = armour.attrs['damage_resist']
                else:
                    dam_res = 0
                dam_res += self.player.stats.get('defense')//25
                hp_loss = random.randint(2, int(self.enemy.attack))-dam_res if random.randint(0, 10) != 0 else 0
                # Jokingly nullify damage if you are insanely overpowered
                if hp_loss <= 0:
                    text += '\nThe {} hits you, but your armour nullifies the damage!'.format(self.enemy.name)
                else:
                    # If the hp loss is positive though, you still have to take it.
                    self.player.stats['health'] -= hp_loss
                    text += '\nThe {} hits you for {} damage!'.format(self.enemy.name, hp_loss)

            if self.enemy.hp <= self.init_enem_hp*0.3:
                # If the enemy is at or below 30% health then tell the user that
                text += '\nThe {} seems to be getting weaker.'.format(self.enemy.name)

            noticed = True

            if conn:
                conn.send(('text|'+str(self.enemy.hp)+text+'\n\n(1) Attack\n(2) Items\n(3) Run\n').encode())
            else:
                printf(text+'\n\n(1) Attack\n(2) Items\n(3) Run\n')
