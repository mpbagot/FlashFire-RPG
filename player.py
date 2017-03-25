import random
import re
from effects import *
from items import *
try:
    import nltk
    has_nltk = True
except:
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
        self.contents = []
        self.generateContents(seed, give_gold)
        self.equipped = {'left':None, 'right':None, 'armour':None}
        self.player = name

    def __len__(self):
        return len(self.contents)

    def modify(self, over_lan=False, conn=None):
        '''
        Run an inventory interface screen
        '''
        # Initialise the empty variables
        text = ''
        hp_change = 0
        while True:
            # If playing singleplayer
            if not over_lan:
                # Do standard print and input
                printf(text)
                comm = inputf('|-Inv Command-> ').split()
            # If playing on a server
            else:
                # Send and recieve from the client
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
                except ValueError:
                    # Catch if the item name was used instead of the item's index
                    text = 'That\'s not an Index number! Please use the Item\'s index, not name.'
                    continue
                if comm[0] in ('drop','equip'):
                    try:
                        x = comm[2]
                    except IndexError:
                        text = ('Invalid command options!')
                        continue

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
                elif item.type not in ('weapon', 'shield', 'spell', 'clothes'):
                    text = ('You can\'t equip that!')
                    continue
                # If everything is all sweet then equip the item
                else:
                    # Print out a nice message to the user
                    if spot == "armour":
                        text = "Equipped {} as armour.".format(item.attrs.get('name'))
                    else:
                        text = 'Equipped {} in {} hand.'.format(item.attrs.get('name'), spot)
                    self.equipped[spot] = item

            elif comm[0] == 'drop':
                quant = int(comm[2])
                # Drop the given quantity if you have enough in your inventory
                if self.contents[int(comm[1])-1][1] > quant:
                    # Print a nice message
                    text = ('Dropping {} {}'.format(quant, item.attrs['name']))
                    # create a list from the itemstack tuple
                    x = list(self.contents[int(comm[1])-1])
                    x[1] -= quant
                    # Iterate the quantity and re-set the tuple
                    self.contents[int(comm[1])-1] = tuple(x)
                else:
                    # Drop the whole stack if the quantity is too great
                    text = ('Dropping all {}'.format(item.attrs['name']))
                    del self.contents[int(comm[1])-1]

            elif comm[0] == 'eat':
                if item.type == 'food':
                    # Always eat 1 of any food
                    quant = 1
                    # Eat the food, reducing the stack quantity
                    if self.contents[int(comm[1])-1][1] > 1:
                        x = list(self.contents[int(comm[1])-1])
                        x[1] -= quant
                        self.contents[int(comm[1])-1] = tuple(x)
                    # or if it's the last bit of food in the stack, then just delete the stack
                    else:
                        del self.contents[int(comm[1])-1]
                    # Add the players health
                    hp_change += item.attrs['h_restore']
                    n = item.attrs.get('name')
                    # Print a nice helpful message
                    text = 'You eat a{} {}'.format('n' if n[0] in 'AEIOU' else '', n)
                else:
                    # Error if it's not food
                    text = ('You can\'t eat that!')
            # Quit the inventory modification menu
            elif comm[0] in ('done', 'exit', 'quit'):
                if over_lan:
                    # Send the hp change to the client
                    conn.send('{}|exit'.format(hp_change).encode())
                else:
                    # otherwise just return the hp change
                    return hp_change
                break
            # Error message if it's an invalid command
            else:
                text = 'Invalid Command!'

    def count(self, name):
        '''
        Return the quantity of a given item in your inventory
        '''
        item = Item.get(name)
        if item == None:
            return
        item = int(item)
        for a in self.contents:
            if a[0] == item:
                return a[1]
        return 0

    def add(self, name, quant):
        '''
        Add the given item at the given quantity to the inventory
        '''
        # Get the item id based on name
        item = Item.get(name)
        if item == None:
            return
        # convert the string item id to an int
        item = int(item)
        # Create an item stack tuple, i.e (item_id, quantity)
        item = (item, quant)
        for i, a in enumerate(self.contents):
            # Loop through the contents to see if the quantity can be added to a preexisting stack
            if a[0] == item[0]:
                # Unpack the tuple into a list (for mutability)
                new_item = list(a)
                # Iterate the quantity
                new_item[1] += quant
                # Repack into a tuple and set back into the inventory.
                self.contents[i] = tuple(new_item)
                return
        # Otherwise append the stack to the contents
        self.contents.append(item)

    def get_combat(self):
        '''
        Get a sub-inventory of all items usable in combat
        '''
        contents = []
        for a in self.contents:
            if Item(*a).attrs['type'] in ('food','spell'):
                contents.append(a)
        inv = Inventory('1'*64, self.player, False)
        inv.equipped = self.equipped
        inv.contents = contents
        return inv

    def generateContents(self, seed, give_gold):
        '''
        Randomly populate an Inventory.
        '''
        i = 0
        while i < getRandomStat(seed):
            # Get a random number (item_id) for the item
            item_id = getRandomStat(seed, 2)
            # Add 1 of that item to the inventory
            if item_id < 15:
                item = Item(item_id, 1)
                self.add(item.attrs['name'].lower(), 1)
                i += 1

        if give_gold:
            # If not playing on hard, then give 30 starting gold
            self.contents.append((0, 30))
        # Sort all the items by item_id for simplicity
        self.contents.sort()

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

    def has_item(self, item_id):
        for item in self.contents:
            if item[0] == item_id:
                return True
        return False

class Player:
    def __init__(self, seed, name, pos, give_gold=True):
        self._seed = seed
        self.stats = self.generateStats(seed)
        self.xp = 0
        self.name = name
        self.pos = pos
        self.current_quests = []
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

    def get_stats(self):
        '''
        Generate a little Stats table for status screen
        '''
        stats = []
        # iterate the stats dictionary
        for i, stat in enumerate(self.stats):
            if stat not in ('max_health', 'health'):
                # Adjust the stat name
                stat_fix = ' '.join(stat.split('_'))
                # Add the stat to the array
                stats.append(stat[0].upper()+stat_fix[1:]+': {}'.format(self.stats[stat]))
        stats.sort()
        stats[2], stats[-1] = stats[-1],stats[2]
        # Join the string and return
        return '\n'.join(stats)

    def has_correct_funds(self, cost):
        '''
        Check if the player has a quantity of Gold more than
        or equal to the given cost.
        '''
        for i in self.inventory.contents:
            if i[0] == 0 and i[1] >= cost:
                return True
        return False

    def remove_funds(self, cost):
        '''
        Remove a given value of Gold equal to the given cost.
        '''
        # Iterate the itemstacks
        for j, i in enumerate(self.inventory.contents):
            if i[0] == 0:
                # if the stack contains Gold and has
                # a greater quantity than the cost
                if i[1] > cost:
                    x = list(self.inventory.contents[j])
                    x[1] -= cost
                    # De-iterate the quantity and re-set the itemstack
                    self.inventory.contents[j] = x
                else:
                    # Since the has_correct_funds() is always run first,
                    # we can just del the itemstack if quantity is equal to cost.
                    del self.inventory.contents[j]

    def level_up(self, should_print=False):
        '''
        Update the value of the player's statistics based on current xp
        '''
        # get the current level + 1
        n = self.stats['level'] + 1
        # While the experience required to get to the next level is less than current xp
        while (n**2+n) <= self.xp:
            # Level up
            self.stats['level'] = n
            if should_print:
                printf('You are now Level {}!'.format(n))
            for stat in self.stats:
                # And increase all of the player's current stats
                if stat != 'level':
                    self.stats[stat] += 2
            n += 1

    def on_end_battle(self):
        '''
        Update the changes to a current quest after a victory in battle
        '''
        for i, quest in enumerate(self.current_quests):
            if not quest.is_recovery and quest.is_eligible_for_update(self.pos):
                self.current_quests[i].current_kill_count += 1
                return

    def __str__(self):
        return '/ {} / HP: {} / Co-ords: {} /'.format(self.name, str(self.stats['health'])+'/'+str(self.stats['max_health']), self.pos)

    def get_save_string(self):
        '''
        Generate the string of data for saving the game
        '''
        return '{}|{}|{}|{}|{}|{}'.format(self._seed, self.name, self.pos, self.stats, self.xp, self.encode_quests())

    @staticmethod
    def get_by_string(string):
        '''
        Generate a Player object from a save string
        '''
        line = string.split('|')
        # Initialise a new Player object
        p = Player(line[0], line[1], eval(line[2]))
        p.stats = eval(line[3])
        p.xp = int(line[4])
        p.current_quests = eval(line[5])
        for a in range(len(p.current_quests)):
            p.current_quests[a] = Quest.get_by_string(p.current_quests[a], p)
        # Set the stats and return
        return p

    def encode_quests(self):
        quests = []
        for q in self.current_quests:
            quests.append(str(q))
        return quests

class Dialogue2:
    def __init__(self, player, node, npc, name=None):
        self.g_speech = npc.gender
        self.n_age = npc.age
        a = ('M', 'F')
        if random.randint(0, 80) == 0:
            self.g_speech = a[(a.index(npc.gender)+1)%2]

        self.g_speech += 'ale' if npc.gender == 'M' else 'emale'

        # Get NPC variables
        self.npc = npc
        self.g_name = npc.name
        self.in_strife = npc.has_quest
        # Get player variables
        self.p_name = player.name
        self.player = player

        self.area = node.typ
        if self.area == 'Town':
            self.tree = Tree.get_generic_quest_tree(self.g_speech)
        else:
            if not name:
                self.tree = Tree.get_generic_tree(self.g_speech, True if isinstance(self.in_strife, str) else self.in_strife)
            else:
                self.tree = Tree.get_tree(name)
        self.layers = []
        self.up = 0

    def start_talk(self):
        '''
        Say a simple statement to begin
        '''
        text = ''
        # For each reply
        for i, a in enumerate(self.tree):
            # return what it could be back
            text += '({}) {}\n'.format(i+1, a[0][0])

        return self.g_name+': ...\n\n'+text

    def respond(self, num):
        '''
        Recurse another layer into the dialogue tree and respond as neccessary
        '''

        if self.up:
            # If the dialogue tree has requested a reversal in the tree,
            # Then cut the layers to shift position back up the tree
            self.layers = self.layers[:-(self.up)]
            self.up = 0

        t = self.tree
        # Iterate and cut down to the current tree layer
        for a in self.layers:
            # Keep getting the next layer down
            t = t[a][2]

        # Add the speech index for the next layer
        self.layers.append(int(num)-1)
        text = ''
        # If the tree hasn't hit the end then print possible reply options
        if not self.is_finished() and self.is_finished() != '':
            t = self.tree
            for a in self.layers[:-1]:
                t = t[a][2]

            # If the dialogue tree can go down another layer and doesn't have a layer reversal in it
            if isinstance(t[int(num)-1][2][0], tuple) or (isinstance(t[int(num)-1][2][0], str) and not t[int(num)-1][2][0].startswith('up')):
                # For each reply
                for i, a in enumerate(t[int(num)-1][2]):
                    # return what it could be back
                    text += '\n({}) {}'.format(i+1, a[0][0])
            # If the tree has a layer reversal (goes back up several layers after response)
            else:
                # Duplicate the tree
                t2 = self.tree
                for a in self.layers[:-(self.up)]:
                    # Iterate and build the response tree
                    t2 = t2[a][2]
                for i, a in enumerate(t2):
                    # Add the possible replies to a string
                    text += '\n({}) {}'.format(i+1, a[0][0])

        if self.is_finished() == '':
            self.layers = self.layers[:-1]
            # An invalid response number was input
            return 'Invalid response number!\n'+text
        # Grab the reply string
        reply = t[int(num)-1][1]
        # If the string requires formatting (used for inserting dynamic variables)
        if '{}' in reply:
            # Split the string at the caret symbol
            reply = reply.split('^')
            for a in range(len(reply)):
                # Iterate each variable that needs to be formatted in
                # If it's one of the below, then switch it to the required variable
                if reply[a] == 'g_name':
                    reply[a] = self.g_name
                elif reply[a] == 'p_name':
                    reply[a] = self.p_name
            # Format the reply string using the above string inserts
            reply = reply[0].format(*reply[1:])
        if t[int(num)-1][0][0] == 'get quest' and self.npc.has_quest:
            self.player.current_quests.append(Quest(self.player, self.g_name))
            reply = 'Yes, here this bounty notice has the details\nQuest details added to journal.'
            self.npc.has_quest = ''

        if t[int(num)-1][0][0] == 'finish quest':
            # If the player requests to finish a quest
            for i, q in enumerate(self.player.current_quests):
                # Iterate all quests and check if the quest is the right one
                if q.init_pos == self.player.pos and q.npc_name == self.g_name:
                    # Check if it's complete
                    if q.is_complete(self.player):
                        # If so, add the reward gold, remove the quest from the current_quests,
                        # modify the NPC's reply and break the loop
                        self.player.inventory.add('gold', q.reward)
                        del self.player.current_quests[i]
                        # If the player had to recover an item
                        if q.is_recovery:
                            reply = 'You found it! Thank goodness. I dont know what I would have done without it!'
                        # Or if the player had to cull enemies
                        else:
                            reply = "Thank you. I can finally sleep well, knowing I won't be murdered by monsters while I sleep."
                        self.npc.has_quest = False
                    break
            # If the player hasnt been given a task yet
            if self.npc.has_quest and not isinstance(self.npc.has_quest, str):
                reply = 'What task? I haven\'t asked you to do anything'
        return '{}: {}'.format(self.p_name, t[int(num)-1][0][1]) + '\n{}: {}\n'.format(self.g_name, reply) + text

    def is_finished(self):
        '''
        Return if the conversation is over
        '''
        t = self.tree
        for a in self.layers:
            try:
                t = t[a][2]
            except IndexError:
                return ''
                # return None
        if isinstance(t[0], str):
            # If the tree[0] is a string (therefore it has no further layers)
            if t[0].startswith('up'):
                # If the tree[0] is a reversal request then set the self.up
                # to the requested number of layers
                self.up = int(t[0].split('^')[1])
                return False
            return True
        return False

class Tree:
    @staticmethod
    def get_generic_tree(gender, in_strife):
        '''
        Get a generic dialogue tree
        '''
        g = gender.lower()
        # Read the speech file
        f = open('speech.txt').read().split('\n')
        # Wittle down the options based on gender and whether or not it has a quest
        f = [eval(a.split('|')[1]) for a in f if a.startswith('generic_{}'.format(g)) and int(a.split('|')[0][-1])%2 == int(in_strife)]
        # Return one of the trees
        return f[random.randint(0, len(f)-1)]

    @staticmethod
    def get_generic_quest_tree(gender):
        '''
        Get a generic dialogue tree for a story based NPC
        '''
        g = gender.lower()
        # Read the speech file
        f = open('speech.txt').read().split('\n')
        # Wittle down the options to story-based and correct gender
        f = [eval(a.split('|')[1]) for a in f if a.startswith('story_{}'.format(g))]
        return f[random.randint(0, len(f)-1)]


    @staticmethod
    def get_tree(name):
        '''
        Get a dialogue tree by name (used for story NPC's)
        '''
        for line in open('speech.txt').read().split('\n'):
            # Iterate and check if the tree on this line has the correct name
            if line.startswith(name):
                return eval(line.split('|')[1])
        # Return a generic tree if the named tree cant be found
        return Tree.get_generic_tree('male', False)

class Trade:
    def __init__(self, player, node, p2=None):
        self.player = player
        self.area = node
        if p2:
            self.player2 = p2
        self.is_mp = bool(p2)
        self.store = node.store if node.store else Store(player.stats['level'])

    def has_item(self, name):
        '''
        Return if the store has a given item
        '''
        for item in self.store.items:
            i = Item(*item)
            if i.attrs.get('name').lower() == name:
                return True
        return False

    def get_item_cost(self, name):
        '''
        Return the cost of an item with a given name
        '''
        for item in self.store.items:
            i = Item(*item)
            if i.attrs.get('name').lower() == name:
                return i.cost
        return 0

    def run_trade(self, game, conn=None, id=None):
        '''
        Loop and run the trade routine
        '''
        text = (str(self.store))
        if conn:
            # If playing as a client
            p = game.players[id]
            conn.send((text+'|0').encode())
            response = conn.recv(4096).decode()
        else:
            # If playing singleplayer
            p = game.player
            printf(text)
            response = input('>>> ').lower()

        while response not in ('leave', 'exit'):
            # While the player doesn't type leave or exit keep handling commands
            if response.startswith('show'):
                # Display the stores contents
                text = (str(self.store))
            # Purchase an item from the store
            elif response.startswith('buy'):
                name = ' '.join(response.split()[1:])
                # Check if the store has the item in stock
                if self.has_item(name):
                    cost = self.get_item_cost(name)
                    # Get the cost and check if the player is rich enough
                    if p.has_correct_funds(cost):
                        # Remove the Gold and add the chosen item
                        p.remove_funds(cost)
                        p.inventory.add(name, 1)
                        # Print a confirmation message
                        text = ('You purchased a{} {}'.format('n' if name[0] in 'aeiou' else '', name))

                    elif self.has_item(name):
                        # If the store has the item but the player doesn't have enough gold
                        text = ('You don\'t have enough Gold for that!')
                else:
                    # Or if the store doesn't have the item
                    text = ('We don\'t sell that here.')
            else:
                # Have the storekeeper be confused otherwise
                text = 'Storekeeper: Huh?'

            if conn:
                # send the text to be printed to the client
                conn.send((text+'|0').encode())
                # Get the client's response
                response = conn.recv(4096).decode()
            else:
                # Just print and get a normal input if playing Singleplayer
                printf(text)
                response = input('>>> ').lower()
        if conn:
            # Transmit a goodbye statement to the client
            conn.send(('Storekeeper: Come again!|0').encode())
            # Update the specific player object
            game.players[id] = p
            return
        # print the goodbye statement
        printf('Storekeeper: Come again!')
        # Update the singleplayer player
        game.player = p

class Quest:
    '''
    A class to handle the status of a non-story randomly-generated quest.
    '''
    def __init__(self, player, npc_name):
        self.player = player
        self.npc_name = npc_name
        self.init_pos = list(player.pos)
        self.level = player.stats['level']+1
        self.is_recovery = random.randint(0, 10) == 0
        if self.is_recovery:
            self.item_to_recover = round(random.randint(1, 5) * self.level)
        else:
            self.enemies_to_kill = random.randint(2,4)*self.level
            self.enemies_to_kill = 1
            self.current_kill_count = 0
        self.reward = round(random.randint(10, 20)*self.level)

    def is_complete(self, player):
        '''
        Return whether the player has fulfilled the requirements of the quest
        '''
        if self.is_recovery:
            return player.has_item(self.item_to_recover)
        else:
            return self.current_kill_count >= self.enemies_to_kill

    def is_eligible_for_update(self, pos):
        '''
        Check if the player is close enough to the initial area (used for enemy culling missions)
        '''
        if self.is_recovery:
            return True
        return get_distance_between(self.init_pos, pos) < 30 and self.current_kill_count <= self.enemies_to_kill

    def __str__(self):
        '''
        Generate the string for saving a quest.
        '''
        if self.is_recovery:
            return '{}%{}%{}%{}%{}'.format(self.npc_name, self.init_pos, int(self.is_recovery), self.item_to_recover, self.reward)
        return '{}%{}%{}%{}%{}%{}'.format(self.npc_name, self.init_pos, int(self.is_recovery), self.current_kill_count, self.enemies_to_kill, self.reward)

    @staticmethod
    def get_by_string(string, player):
        '''
        Get a Quest object by a string and player.
        '''
        string = string.split('%')
        q = Quest(player, '')
        q.npc_name = string[0]
        q.init_pos = eval(string[1])
        q.is_recovery = bool(int(string[2]))
        if not q.is_recovery:
            q.current_kill_count = int(string[3])
            q.enemies_to_kill = int(string[4])
        else:
            q.item_to_recover = int(string[3])
        q.reward = int(string[-1])
        return q
