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
    def __init__(self, seed, name):
        self.contents = self.generateContents(seed)
        self.player = name

    def generateContents(self, seed):
        '''
        Randomly populate an Inventory.
        '''
        conts = []
        for a in range(getRandomStat(seed)):
            item_id = getRandomStat(seed, 2)
            conts.append((item_id, 1))
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
            text += '{}{}\n'.format(i+1, str(item))
        return text

class Player:
    def __init__(self, seed, name, pos):
        self._seed = seed
        self.stats = self.generateStats(seed)
        self.name = name
        self.pos = pos
        self.inventory = Inventory(seed, name)

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
