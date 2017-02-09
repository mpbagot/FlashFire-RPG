import random
import re

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

class Dialogue:
    def __init__(self, player, node, npc):
        self.g_speech = npc.gender
        a = ('M', 'F')
        if random.randint(0, 80) == 0:
            self.g_speech = a[(a.index(npc.gender)+1)%2]
        self.g_name = npc.name
        self.in_strife = npc.has_quest
        self.p_name = player.name
        self.area = node.typ
        self.is_afraid = player.name not in npc.known_players
        self.far_from_civ = node.typ != 'city'

        self.line_log = []
        self.known_facts = {}

    def respond(self, res):
        '''
        Respond to a given input statement
        '''
        text = 'What you just said makes no sense.'
        if self.is_question(res):
            # This is true if res is just a question
            text = self.parse_question(res)
        else:
            words = re.findall(r'\w', res)
            # The text is either a conditional statement + (question or statement) or just simply a statement.
            if words[0] in ('if', 'for', 'where', 'in'):
                # Starts with a conditional statement, parse the question relative to it
                condition = res.split(',')[0]
                station = res.split(',')[1]
                # Check if station is a statement or question
                if not self.is_question(station):
                    text = self.parse_statement(station, condition)
                else:
                    text = self.parse_question(station, condition)

            else:
                # The sentence is just a plain statement
                text = self.parse_statement(res)

        if res == "Goodbye":
            self.is_finished = self._meh
            text = 'Goodbye.'
        return '{}: {}'.format(self.g_name, text)

    def _meh(self):
        '''
        Stand in function to be swapped with is_finished.
        and yes, I do realise I could do this more easily.
        '''
        return True

    def is_question(self, res):
        words = re.findall(r'\w+', res)
        print(words)
        if words[0] in ('who', 'what', 'when', 'where', 'why', 'how', 'are', 'is', 'isn\'t', 'isnt' 'will'):
            if words[0] == 'will':
                # If this is true then it'S a valid 'will something' question
                return (words[1] in ('you', 'i', 'it', 'they', 'those', 'the', 'that') or (words[0][0].isupper() and words[0][1:].islower()))
            else:
                # If it's a valid question, not starting with 'will'
                return True
        else:
            return False
            # The text is either a conditional statement + (question or statement) or just simply a statement.

    def parse_question(question, condition=None):
        # TODO determine the result, either based on condition
        # or not, and return the answer
        return 'parsing question'

    def parse_statement(question, condition=None):
        # TODO store the information and say some remark about it.
        return 'parsing statement'

    def is_finished(self):
        '''
        A function to determine if the dialogue has finished.
        '''
        return False

    def start_talk(self):
        '''
        Begin the talk with the NPC.
        '''
        if self.is_afraid:
            return ('{}: ...'.format(self.g_name))

        else:
            if self.g_speech == 'M':
                return (self.g_name+": Welcome back, {}. {}".format(self.p_name, 'Willing to help now?' if self.in_strife else ''))
            else:
                return (self.g_name+': Hello, {}. {}'.format(self.p_name, 'I do need still your help, if you are willing to offer it.' if self.in_strife else ''))
