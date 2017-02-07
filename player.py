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
        return int(seed[random.randint(0, 63)])
    s = ''
    start = random.randint(0, 63-chars-1)
    s += seed[start:start+chars]
    return int(s)

def isnum(n):
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
        conts.sort()
        return conts

    def __str__(self):
        towrite = [str(Item(i, q)) for i, q in self.contents]
        return '\n'.join(towrite)

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
        stats['health'] = getRandomStat(seed, 2)
        stats['defense'] = getRandomStat(seed, 2)
        stats['attack'] = getRandomStat(seed, 2)
        stats['trade_skill'] = getRandomStat(seed, 2)
        stats['speed'] = getRandomStat(seed, 2)
        stats['level'] = 1
        return stats

    def __str__(self):
        return '{} | Stats: {} | Co-ords: {}'.format(self.name, str(self.stats), self.pos)

    def get_save_string(self):
        '''
        Generate the string of data for saving the game
        '''
        return '{}|{}|{}|{}'.format(self._seed, self.name, str(self.pos), str(self.stats))

    @staticmethod
    def get_by_string(string):
        line = string.split('|')
        p = Player(line[0], line[1], eval(line[2]))
        p.stats = eval(line[3])
        return p
