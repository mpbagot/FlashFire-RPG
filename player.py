import random
from effects import *
from items import *

def genSeed(text):
    '''
    Generate an all-integer seed from a Hexadecimal hash.
    '''
    s = []
    for a in text:
        if isnum(a):
            s.append(a)
        else:
            s.append(str(ord(a))[-1])
    return ''.join(s)

def getRandomStat(seed, chars=None):
    '''
    Get a random number, partially based of seed.
    '''
    if chars is None:
        # Return a single character from the seed as an int
        return int(seed[random.randint(0, 63)])
    s = ''
    # Pull a random segment of the seed, 'chars' characters long
    start = random.randint(0, 63-chars-1)
    s += seed[start:start+chars]
    return int(s)

def isnum(n):
    '''
    Check if an input string is a valid integer
    '''
    try:
        int(n)
        return True
    except:
        return False

class Inventory:
    def __init__(self, seed, name, give_gold):
        self.contents = self.generateContents(seed, give_gold)
        self.equipped = {'left':None, 'right':None, 'armour':None}
        self.player = name

    def modify(self, over_lan=False, conn=None):
        text = ''
        while True:
            print(text)

            if not over_lan:
                print(text)
                comm = inputf('|-Inv Command-> ').split()
            else:
                print(text)
                conn.send(text.encode())
                comm = conn.recv(1024).decode()

            if comm[0] in ('equip', 'drop', 'eat'):
                try:
                    # Try to get the item
                    item = Item(*self.contents[int(comm[1])-1])
                except IndexError:
                    # Or error if you dont have that item in the inventory
                    text = ('There\'s no Item with that Item Index.')
                    print('error!!!')
                    continue

            if comm[0] == 'show inv':
                # return the inventory string, just like with the show status command
                text = self.__str__()

            elif comm[0] == 'equip':
                spot = comm[2]
                # Check if given spot is valid
                if spot not in ('armour', 'left', 'right'):
                    text = ('Invalid Equipment Spot!')
                    continue
                # Check that all item types are valid
                elif spot == 'armour' and item.type != 'clothes':
                    text = ('You can\'t wear that!')
                    continue
                elif item.type not in ('weapon', 'shield', 'spell'):
                    text = ('You can\'t equip that!')
                    continue
                # If everything is all sweet then equip the item
                else:
                    self.equipped[spot] = item

            elif comm[0] == 'drop':
                quant = int(comm[2])
                # Drop the given quantity if you have enough in your inventory
                if self.contents[int(comm[1])-1][1] > quant:
                    text = ('Dropping {} {}'.format(quant, item.attrs['name']))
                    self.contents[int(comm[1])-1][1] -= quant
                else:
                    # Drop the whole stack if the quantity is too great
                    text = ('Dropping all {}'.format(item.attrs['name']))
                    del self.contents[int(comm[1])-1]
                print(text)

            elif comm[0] == 'eat':
                if item.type == 'food':
                    # Eat the food, reducing the stack quantity
                    if self.contents[int(comm[1])-1][1] > 1:
                        self.contents[int(comm[1])-1][1] -= 1
                    else:
                        del self.contents[int(comm[1])-1]
                    # Add and stabilise the players health
                    self.player.stats['health'] += item.attrs['h_restore']
                    self.player.stats['health'] = self.player.stats['max_health']
                else:
                    # Error if it's not food
                    text = ('You can\'t eat that!')
            # Quit the inventory modification menu
            elif comm[0] in ('done', 'exit', 'quit'):
                break

    def generateContents(self, seed, give_gold):
        '''
        Randomly populate an Inventory.
        '''
        conts = []
        for a in range(getRandomStat(seed)):
            item_id = getRandomStat(seed, 2)
            conts.append((item_id, 1))
        if give_gold:
            conts.append((0, 30))
        conts.sort()
        return conts

    def __str__(self):
        '''
        Create an directly printable string for the status command
        '''
        # Generate an Item() object list
        inv = [Item(*a) for a in self.contents]
        text = 'Inventory:\n'
        # Iterate and create a string list of the Items in this inventory
        for i, item in enumerate(inv):
            x = '{} - {}'.format(i+1, str(item))
            x += ' '*(40-len(x))
            if i%2 == 1:
                x += '\n'
            text += x

        return text

class Player:
    def __init__(self, seed, name, pos, give_gold=True):
        self._seed = seed
        self.stats = self.generateStats(seed)
        self.name = name
        self.pos = pos
        self.inventory = Inventory(seed, name, give_gold)

    def generateStats(self, seed):
        '''
        Randomly generate starting stats for a player
        '''
        stats = {}
        #Set random numbers and add them to a stats dictionary
        stats['max_health'] = getRandomStat(seed, 2)
        stats['health'] = stats['max_health']
        stats['defense'] = getRandomStat(seed, 2)
        stats['attack'] = getRandomStat(seed, 2)
        stats['trade_skill'] = getRandomStat(seed, 2)
        stats['speed'] = getRandomStat(seed, 2)
        stats['level'] = 1
        return stats

    def __str__(self):
        return '/ {} / HP: {} / Co-ords: {} /'.format(self.name, str(self.stats['health'])+'/'+str(self.stats['max_health']), self.pos)

    def get_save_string(self):
        '''
        Generate the string of data for saving the game
        '''
        return '{}|{}|{}|{}'.format(self._seed, self.name, str(self.pos), str(self.stats))

    @staticmethod
    def get_by_string(string):
        '''
        Generate a Player object from a save string
        '''
        line = string.split('|')
        # Initialise a new Player object
        p = Player(line[0], line[1], eval(line[2]))
        p.stats = eval(line[3])
        # Set the stats and return
        return p
