import random

class Enemy:
    def __init__(self, dif_ml, pos):
        self.pos = pos
        self.attack = random.randint(1,3)*dif_ml
        self.hp = random.randint(1, 10)*dif_ml

    def __str__(self):
        '''
        Create the string to save entity data
        '''
        return '{}?{}?{}'.format(str(self.pos), self.attack, self.hp)

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
