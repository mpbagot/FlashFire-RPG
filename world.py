import random
from entity import *
import time
from threading import Thread
from multiprocessing import Pool,Process
import sys

# pool = Pool()

class World:
    def __init__(self, x, y, difficulty, lod, pos=[], gen=True):
        self.diff = difficulty
        self.lod = lod
        self.chunk_array = [[0 for b in range(x//10)] for a in range(y//10)]
        if gen:
            #Generate an empty array
            if pos != []:
                self.s_chunk = [(pos[0]//10)-2, (pos[1]//10)-2]
                self.generate_start(difficulty, lod)
                sys.stdout.write('World Generation complete!\n')

            self.t = Thread(target=self.generate_world, args=(x,y, difficulty, lod))
            self.t.daemon = True
            self.t.start()

    def generate_start(self, difficulty, lod):
        x,y = self.s_chunk[0], self.s_chunk[1]
        for a in range(5):
            for b in range(5):
                if x+b < 99 and y+a < 99:
                    if self.chunk_array[y+a][x+b] == 0:
                        self.chunk_array[y+a][x+b] = self.make_chunk(x+b, y+a, difficulty, lod)

    def generate_world(self, x, y, difficulty, lod, show_bar=False):
        # Loop the chunk array
        if show_bar:
            sys.stdout.write('[')
            sys.stdout.flush()
        for i in range(y//10):
            if show_bar and i%3 == 0:
                sys.stdout.write('#')
                sys.stdout.flush()
            for j in range(x//10):
                # And populate it with Chunks
                if self.chunk_array[j][i] == 0:
                    self.chunk_array[j][i] = self.make_chunk(j, i, difficulty, lod)
                    # print('Generating incomplete chunk...')
        if show_bar:
            sys.stdout.write(']\n')
            sys.stdout.flush()

    @staticmethod
    def generate_from_file(details, pos=[1, 1]):
        '''
        Load the world array from a saved file
        '''
        # TODO fix loading from file speed and accuracy
        w = World(len(details)*10, len(details[0])*10, 0, 0, gen=False)
        y = len(details)
        x = len(details[0])
        num = 0
        for row in range(y):
            if row%3 == 0 and row != 0:
                num += 1
            for chunk in range(x):
                #fill the given chunk with a generated chunk
                w.chunk_array[row][chunk] = Chunk.get_by_string([row, chunk], eval(details[row][chunk]), w)
                print('[{}{}]'.format(num*'#', (33-num)*'-'), end='\r')
        print()
        t = Thread(target=w.generate_world, args=(x, y, 'medium', 2))
        t.daemon = True
        t.start()
        return w

    def get_save_string(self):
        '''
        Get the string used to save the node in the save file
        '''
        array = [[str(self.get_chunk(x,y)) for x in range(len(self.chunk_array))] for y in range(len(self.chunk_array))]
        return str(array)

    def get_description(self, pos):
        return self.get_node(pos[0],pos[1]).get_description()

    def make_chunk(self, x, y, diff, lod):
        chunk = Chunk([x,y])
        for a in range(10):
            for b in range(10):
                chunk.array[b][a] = self.make_node(chunk, a, b, diff, lod)
        return chunk

    def make_node(self, chunk, x, y, dif, lod):
        '''
        Generate a new random area nodes
        '''
        dc = {'easy':1, 'medium':2, 'hard':4.5}
        #generate passage in a variety of directions based on
        #surrounding nodes and randomness
        hasNorth = hasSouth = hasEast = hasWest = False
        while [hasNorth, hasSouth, hasEast, hasWest].count(True) < 2:
            # If we are not on the far left then
            # check if the node to the east allows westward motion or randomly create a passage
            if x > 0:
                if random.randint(0, 5) == 0 or chunk.get_node(x-1,y).hasEast:
                    hasWest = True
            # Create an inter-chunk passage to the west if not on the world border and pass random check
            elif random.randint(0, 3) != 0 and not chunk.is_far_west():
                hasWest = True
            # Same as the top except for the eastward passage
            if x < 9:
                if random.randint(0, 5) == 0:
                    hasEast = True
            # Create an inter-chunk passage to the east if not on the world border and pass random check.
            elif random.randint(0, 3) != 0 and not chunk.is_far_east():
                hasEast = True

            # Literally the same as all above except for north/south motion
            if y > 0:
                if random.randint(0, 5) == 0 or chunk.get_node(x,y-1).hasSouth:
                    hasNorth = True
            elif random.randint(0, 3) != 0 and not chunk.is_far_north():
                hasNorth = True
            if y < 9:
                if random.randint(0, 5) == 0:
                    hasSouth = True
            elif random.randint(0, 3) != 0 and not chunk.is_far_south():
                hasSouth = True

        #Generate randomly difficult enemies based on difficulty
        enemies = []
        if random.randint(1,9)//dc[dif] == 1:
            for a in range(random.randint(0, int(dc[dif]))):
                enemies.append(Enemy(dc[dif], [x,y]))

        #generate a type for the node, generates cities in blocks
        types = ['forest', 'desert', 'grass_plains']
        # Check if a city is nearby and keep generating it.
        i = x > 0 and y > 0 and chunk.get_node(x-1, y-1).typ == 'city'
        j = x > 0 and chunk.get_node(x-1, y).typ == 'city'
        k = y > 0 and chunk.get_node(x,y-1).typ == 'city'
        if (i or j or k) and random.randint(0, 3) != 0:
            typ = 'city'
        else:
            # If not a city then possibly add a city or just pick an area type
            if random.randint(0, 1000) == 0:
                typ = 'city'
            else:
                typ = types[random.randint(0,2)]

        # spawn npc's randomly and populate this list.
        npc = []
        pos = (x, y)
        if typ != 'city' and random.randint(0, 5)//dc[dif] > 0:
            for a in range(random.randint(0, 4)):
                npc.append(NPC(pos))

        # Return the generated Area_Node object
        return Area_Node(hasNorth, hasSouth, hasEast, hasWest, enemies, typ, npc)

    def set_node(self, pos, **kwargs):
        x,y = pos
        for var in kwargs:
            if var == 'store':
                self.chunk_array[y//10][x//10].array[y%10][x%10].store = kwargs['store']

    def get_node(self, x, y):
        '''
        Get a node at the given world coordinates
        '''
        try:
            chunk = self.chunk_array[y//10][x//10]
            if not chunk:
                self.chunk_array[y//10][x//10] = self.make_chunk(x//10,y//10,2,2)
            return self.chunk_array[y//10][x//10].array[y%10][x%10]
        except AttributeError:
            raise Exception(str((x,y)))

    def get_chunk(self, x, y):
        '''
        Get the chunk at the given world coordinates
        '''
        return self.chunk_array[y//10][x//10]

class Chunk:
    def __init__(self, pos):
        self.pos = pos
        self.array = [[0 for a in range(10)] for b in range(10)]

    def get_node(self, x, y):
        '''
        Get a node within the chunk's node array
        '''
        return self.array[y][x]

    @staticmethod
    def get_by_string(pos, details, w):
        '''
        Get a chunk object from a save string
        '''
        chunk = Chunk(pos)
        if details != 0:
            for i, row in enumerate(details):
                for j, node in enumerate(row):
                    # Add a loaded node to the array
                    chunk.array[i][j] = Area_Node.get_by_string(node)
        else:
            chunk = 0
        #     chunk = w.make_chunk(*chunk.pos, 'medium', 2)
        return chunk

    def __str__(self):
        '''
        Generate a string for saving the chunk
        '''
        array = [[str(self.array[b][a]) for a in range(len(self.array[0]))] for b in range(len(self.array))]
        return str(array)

    def is_far_south(self):
        '''
        Determine if the chunk is on the southern edge of the world
        '''
        return self.pos[1] == 999

    def is_far_north(self):
        '''
        Determine if the chunk is on the northern edge of the world
        '''
        return self.pos[1] == 0

    def is_far_east(self):
        '''
        Determine if the chunk is on the eastern edge of the world
        '''
        return self.pos[0] == 999

    def is_far_west(self):
        '''
        Determine if the chunk is on the western edge of the world
        '''
        return self.pos[0] == 0

class Area_Node:
    def __init__(self, n, s, e, w, enemies, typ, npc):
        self.typ = typ
        self.enemies = enemies
        self.npc = npc
        self.hasNorth, self.hasSouth = (n,s)
        self.hasEast, self.hasWest = (e,w)
        self.store = None
        self.desc_index = None

    def get_description(self):
        '''
        Get the description text to display when player looks around
        '''
        string = ''
        with open('desc.txt') as f:
            # Load the description dictionary
            l = [a.split('|') for a in f.read().split('\n') if a != '']
            dc = {a[0]:a[1:] for a in l}

        d2 = {'North':self.hasNorth, 'South':self.hasSouth, 'East':self.hasEast, 'West':self.hasWest}
        # Get the passage description based on the movable directions
        if all([d2[a] for a in d2]):
            string += '\nThere are passage\'s in all directions.'
        else:
            for a in d2:
                if d2[a]:
                    # If the direction is travelable (?) then add the notification to the description string
                    if string and string[-1] not in ('.', '\n'):
                        string += ', another leads to the {}.'.format(a)
                        continue
                    string += '\nA passage leads to the {}'.format(a)
        string += '\n'

        if len(self.npc) == 1:
            # If there's one person nearby then tell the player that
            string += '\nA strange person stands nearby. They appear harmless, but possibly afraid.'
        elif len(self.npc) > 3:
            # If there's a few then tell the player that there is a group
            string += '\nA group of people cower nearby. They seem greatly afraid of something.'

        if len(self.enemies) > 3:
            # If there are lots of enemies then tell the player that they are in trouble!
            string += '\nYou are surrounded by enemies!'
        else:
            # Otherwise just state the number of enemies.
            string += ('\nThere '+('are {} enemies' if len(self.enemies) != 1 else 'is {} enemy')+' nearby.').format(len(self.enemies))
        x = len(dc[self.typ])-1
        if not self.desc_index:
            self.desc_index = random.randint(0, x)
        # Return the area description + the other details.
        return dc[self.typ][self.desc_index] + string

    def __str__(self):
        '''
        Get the save string used in the save file.
        '''
        return '{}{}{}{}/{}/{}/{}'.format(int(self.hasNorth), int(self.hasSouth),
                                       int(self.hasEast), int(self.hasWest),
                                       self.encode_enemies(), self.typ, str([str(a) for a in self.npc]))

    def encode_enemies(self):
        '''
        Encode the enemies data for saving and Loading
        '''
        enems = []
        for a in self.enemies:
            # Convert the enemy object into a string
            enems.append(str(a))
        return str(enems)

    @staticmethod
    def get_by_string(string):
        '''
        Generate a node by pre-saved data
        '''
        #Pull passageway data
        n,s,e,w = (bool(int(string[0])), bool(int(string[1])), bool(int(string[2])), bool(int(string[3])))
        string = string.split('/')[1:]
        #Get the enemies
        enemies = [Enemy.get_by_string(a) for a in eval(string[0])]
        #Get the node area type
        typ = string[1]
        npc = [NPC.get_by_string(a) for a in eval(string[2])]
        return Area_Node(n, s, e, w, enemies, typ, npc)

class Null_Node(Area_Node):
    def __init__(self):
        super().__init__(False,False,False,False,[],'Hills',[])
