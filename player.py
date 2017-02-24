import random
import re
from effects import *
from items import *
try:
    import nltk
    has_nltk = True
except:
    pass
    has_nltk = False

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
        hp_change = 0
        while True:

            if not over_lan:
                printf(text)
                comm = inputf('|-Inv Command-> ').split()
            else:
                conn.send(text.encode())
                comm = conn.recv(1024).decode().split()

            if comm[0] in ('equip', 'drop', 'eat'):
                try:
                    # Try to get the item
                    item = Item(*self.contents[int(comm[1])-1])
                except IndexError:
                    # Or error if you dont have that item in the inventory
                    text = ('There\'s no Item with that Item Index.')
                    continue
                try:
                    x = comm[2]
                except IndexError:
                    text = ('Invalid command options!')

            if comm[0] in ('show', 'list'):
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
                    x = list(self.contents[int(comm[1])-1])
                    x[1] -= quant
                    self.contents[int(comm[1])-1] = tuple(x)
                else:
                    # Drop the whole stack if the quantity is too great
                    text = ('Dropping all {}'.format(item.attrs['name']))
                    del self.contents[int(comm[1])-1]

            elif comm[0] == 'eat':
                if item.type == 'food':
                    # Eat the food, reducing the stack quantity
                    if self.contents[int(comm[1])-1][1] > 1:
                        x = list(self.contents[int(comm[1])-1])
                        x[1] -= quant
                        self.contents[int(comm[1])-1] = tuple(x)
                    else:
                        del self.contents[int(comm[1])-1]
                    # TODO Add and stabilise the players health
                    hp_change += item.attrs['h_restore']
                else:
                    # Error if it's not food
                    text = ('You can\'t eat that!')
            # Quit the inventory modification menu
            elif comm[0] in ('done', 'exit', 'quit'):
                if over_lan:
                    conn.send('{}|exit'.format(hp_change).encode())
                else:
                    return hp_change
                break

    def add(self, name, quant):
        item = Item.get(name)
        item = int(item)
        item = (item, quant)
        for i, a in enumerate(self.contents):
            if a[0] == item[0]:
                new_item = list(a)
                new_item[1] += quant
                self.contents[i] = tuple(new_item)
                return
        self.contents.append(item)

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
        self.in_conversation = False
        self.is_hard = give_gold
        self.inventory = Inventory(seed, name, give_gold)

    def generateStats(self, seed):
        '''
        Randomly generate starting stats for a player
        '''
        stats = {}
        #Set random numbers and add them to a stats dictionary
        hp = getRandomStat(seed, 2)
        while hp < 5:
            hp = getRandomStat(seed, 2)
        stats['max_health'] = hp
        stats['health'] = stats['max_health']
        stats['defense'] = getRandomStat(seed, 2)
        stats['attack'] = getRandomStat(seed, 2)
        stats['trade_skill'] = getRandomStat(seed, 2)
        stats['speed'] = getRandomStat(seed, 2)
        stats['level'] = 1
        return stats

    def has_correct_funds(self, cost):
        for i in self.inventory.contents:
            if i[0] == 0 and i[1] >= cost:
                return True
        return False

    def remove_funds(self, cost):
        for j, i in enumerate(self.inventory.contents):
            if i[0] == 0:
                if i[1] > cost:
                    x = list(self.inventory.contents[j])
                    x[1] -= cost
                    self.inventory.contents[j] = x
                else:
                    del self.inventory.contents[j]

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

class Dialogue:
    def __init__(self, player, node, npc):
        self.g_speech = npc.gender
        self.n_age = npc.age
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
        self.known_facts = []

    def respond(self, res):
        '''
        Respond to a given input statement
        '''
        text = 'What you just said makes no sense.'
        # Add the user-spoken line to the line log
        self.line_log.append(res)

        if self.is_question(res):
            # This is true if res is just a question
            text = self.parse_question(res)
        else:
            words = re.findall(r'\w+', res)
            # The text is either a conditional statement + (question or statement) or just simply a statement.
            if words[0] in ('if', 'for', 'where', 'in'):
                # Starts with a conditional statement, parse the question relative to it
                condition = res.split(',')[0].strip()
                station = res.split(',')[1].strip()
                print(station)
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
        '''
        Determine if the input statement is a question or statement
        '''
        words = re.findall(r'\w+', res)
        if words[0] in ('who', 'would', 'am', 'what', 'when', 'where', 'why', 'how', 'are', 'is', 'isn\'t', 'isnt', 'does', 'do', 'did', 'will'):
            if words[0] == 'will':
                # If this is true then it'S a valid 'will something' question
                return (words[1] in ('you', 'i', 'it', 'they', 'those', 'the', 'that', 'he', 'she') or (words[0][0].isupper() and words[0][1:].islower()))
            else:
                # If it's a valid question, not starting with 'will'
                return True
        else:
            return False
            # The text is either a conditional statement + (question or statement) or just simply a statement.

    def parse_question(self, question, condition=None):
        '''
        Determine what the user is asking and answer if possible
        '''
        # TODO determine the result, either based on condition
        # or not, and return the answer

        if not condition:
            # Parse a standard question without a conditional statement.

            # If the NLTK (Natural Language ToolKit) is installed then use proper parsing
            if has_nltk:
                # Tokenise and Tag the words in the sentence
                sentence = nltk.word_tokenize(question)
                tags = nltk.pos_tag(sentence)

                # Set empty topic and value strings
                topic = ''
                needed_value = ''
                # Iterate and fill in the topic and value tags
                for tag in tags:
                    if tag[1] in ('PRP', 'PRP$', 'NNP'):
                        topic += ' {}'.format(tag[0])
                    elif tag[1] in ('NN', 'JJ'):
                        up_word = tag[0][0].upper()+tag[0][1:]
                        g = nltk.pos_tag(nltk.word_tokenize(up_word))[0][1] == 'NNP'
                        if tag[0][0].isupper() or (tag[1] == 'NN' and topic == '') or (tag[1] == 'JJ' and g):
                            topic += ' {}'.format(tag[0])
                            continue
                        needed_value += tag[0]
                topic = topic.strip()
                # print('Topic is {}, Needed Value is {}'.format(topic, needed_value))

                # Iterate and return the known details on the topic
                for obj in self.known_facts:
                    if obj.name == topic.lower():
                        x = obj.stats.get(needed_value)
                        val = '' if not x else x
                        if not val:
                            for synset in nltk.corpus.wordnet.synsets(needed_value):
                                for lemma in synset.hyponyms():
                                    for word in lemma.lemma_names():
                                        m = obj.stats.get(' '.join(word.split('_')))
                                        if m != None:
                                            val = m
                                            break
                        if val:
                            return val[0].upper() + val[1:]

            # lowercase the question to make checking easier
            q = question.lower()
            if q.startswith('what is your name'):
                # Tell the user the NPC's name
                return 'My name is {}, What\'s your\'s?'
            elif q.startswith('how are you'):
                # Check if there's a problem
                if self.in_strife:
                    # Tell the player about it
                    return 'Actually, I need your help.'
                else:
                    # or just tell them that it's all good.
                    return 'I\'m fine, thank you.'
            elif q.startswith('whats the problem'):
                # Check if we have a quest
                if self.in_strife:
                    # Tell them the quest
                    return 'AAAAHHH!'
                else:
                    # Tell them there's no problem if there isn't one
                    return 'What problem? There\'s nothing for me to worry about.'
        # Act confused if the npc can't respond
        return 'I dont know.'

    def parse_statement(self, statement, condition=None):
        '''
        Determine what the user is telling you and store it as fact,
        even if it's cleary wrong.
        '''
        # If the NLTK is installed then run proper statement parsing
        if has_nltk:
            # TODO store the information and say some remark about it.
            if not condition:
                # Parse a standard statement without a conditional statement.

                # Tokenise and Tag the words in the sentence
                sentence = nltk.word_tokenize(statement)
                tags = nltk.pos_tag(sentence)

                # Set empty topic and value strings
                topic = ''
                stat = ''
                value = ''

                # Iterate and fill in the topic and value tags
                for tag in tags:
                    if tag[1] in ('PRP', 'PRP$', 'NNP'):
                        topic += ' {}'.format(tag[0])
                    elif tag[1] in ('NN', 'JJ'):
                        up_word = tag[0][0].upper()+tag[0][1:]
                        g = nltk.pos_tag(nltk.word_tokenize(up_word))[0][1] == 'NNP'
                        if tag[0][0].isupper() or (tag[1] == 'NN' and topic == '') or (tag[1] == 'JJ' and g):
                            topic += ' {}'.format(tag[0])
                            continue
                        stat += ' '+tag[0]
                    elif tag[1] in ('CD', 'JJ'):
                        value = tag[0]
                topic = topic.strip()
                stat = stat.strip()

                print('Topic is {}, Needed Value is {}'.format(topic, stat))
                statement = [a if a != 'i' else 'you' for a in statement.lower().split()]
                statement = ' '.join(statement)
                obj = Topic(topic.lower(), {stat:statement})
                self.known_facts.append(obj)

            else:
                # Parse a statement taking into account the given condition.
                pass
        # Otherwise just perform some preset responses
        else:
            q = statement.lower()
            # If the person is contemplating suicide then give them a speech on why not to.
            if 'kill yourself' in q or 'kill myself' in q or 'kms' in q or 'kys' in q:
                return open('.talk.txt').read()
            # If they call someone an idiot, tell them that they are mean.
            elif 'idiot' in q and 'not an idiot' not in q:
                return 'You\'re not being very nice.' if random.randint(0, 40) == 0 else 'I agree.'
            # If the user contemplates an unspeakable evil, tell that it it wrong
            # and to leave and never return! (User can still talk to NPC)
            bad_verbs = ('kill', 'murder', 'rape')
            for v in bad_verbs:
                if v+' you' in q:
                    return b[0].upper()+b[1:] + ' is wrong! LEAVE AND NEVER RETURN!!!'
        # Act surprised when no other response can be made
        return ('Really?', 'That\'s amazing!', 'Meh.', 'You\'re a genius!', 'I agree.')[random.randint(0, 4)]

    def is_finished(self):
        '''
        A function to determine if the dialogue has finished.
        '''
        return False

    def start_talk(self):
        '''
        Begin the talk with the NPC.
        '''
        # If the npc doesn't know the player
        if self.is_afraid:
            return ('{}: ...'.format(self.g_name))

        else:
            # If the NPC has a male style of talk
            if self.g_speech == 'M':
                return (self.g_name+": Welcome back, {}. {}".format(self.p_name, 'Willing to help now?' if self.in_strife else ''))
            # If the NPC has a female style of talk
            else:
                return (self.g_name+': Hello, {}. {}'.format(self.p_name, 'I do need still your help, if you are willing to offer it.' if self.in_strife else ''))

class Topic:
    def __init__(self, name, fact):
        self.name = name
        self.stats = fact

class Trade:
    def __init__(self, player, node, p2=None):
        self.player = player
        self.area = node
        if p2:
            self.player2 = p2
        self.is_mp = bool(p2)
        self.store = node.store if node.store else Store(player.stats['level'])

    def has_item(self, name):
        for item in self.store.items:
            i = Item(*item)
            if i.attrs.get('name') == name:
                return True
        return False

    def get_item_cost(self, name):
        for item in self.store.items:
            i = Item(*item)
            if i.attrs.get('name') == name:
                return i.cost
        return 0

    def run_trade(self, game, conn=None, id=None):
        text = (str(self.store))
        if conn:
            p = game.players[id]
            conn.send(text.encode())
            response = conn.recv(4096).decode()
        else:
            p = game.player
            response = input('>>> ').lower()

        while response not in ('leave', 'exit'):
            if response.startswith('show'):
                text = (str(self.store))
            elif response.startswith('buy'):
                name = ' '.join(response.split()[1:])
                if self.has_item(name):
                    cost = self.get_item_cost(name)
                    if p.has_correct_funds(cost):
                        p.remove_funds(cost)
                        p.inventory.add(name, 1)
                        text = ('You purchased a {}'.format(name))

                    elif self.has_item(name):
                        text = ('You don\'t have enough Gold for that!')
                else:
                    text = ('We don\'t sell that here.')
            if conn:
                conn.send(text.encode())
                response = conn.recv(4096).decode()
            else:
                printf(text)
                response = input('>>> ').lower()
        if conn:
            game.players[id] = p
            return
        game.player = p
