import random
from entity import *
from time import sleep
import sys

class World:
    def __init__(self, x, y, difficulty, lod, pos=[], gen=True):
        self.diff = difficulty
        self.lod = lod

        self.init_pos = pos

        self.is_loading = False
        self.details = None

        self.used_names = []

        #Generate an empty array
        self.chunk_array = [[0 for b in range(x//10)] for a in range(y//10)]

    @staticmethod
    def generate_from_file(details, pos=[1, 1]):
        '''
        Load the world array from a saved file
        '''
        # Create an empty world object
        w = World(len(details)*10, len(details[0])*10, 0, 0, gen=False)
        # Set is_loading so that it loads, not generates new chunks
        w.is_loading = True
        # Set the load string array for the world
        w.details = details
        return w

    def get_save_string(self):
        '''
        Get the string used to save the node in the save file
        '''
        array = [[str(chunk) for chunk in row] for row in self.chunk_array]
        return str(array)

    def get_description(self, pos):
        '''
        Get the area description for the node at the given position
        '''
        return self.get_node(pos[0],pos[1]).get_description()

    def make_chunk(self, x, y, diff, lod):
        '''
        Generate a chunk object based on position
        '''
        # Generate an empty Chunk object
        chunk = Chunk([x,y])
        for a in range(10):
            for b in range(10):
                # Iterate the x and y of the array and create nodes to fill it
                # If the node we are making is the very first in the whole game
                if [x*10+a, y*10+b] == self.init_pos:
                    # Then generate the village of Little Ivywood
                    chunk.array[b][a] = self.make_node(chunk, a, b, diff, lod, True)
                    continue
                chunk.array[b][a] = self.make_node(chunk, a, b, diff, lod)
        return chunk

    def make_node(self, chunk, x, y, dif, lod, start=False):
        '''
        Generate a new random area nodes
        '''
        dc = {'easy':1, 'medium':3, 'hard':4.5}
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
        # Remove the or true after testing
        if random.randint(1,9)//dc[dif] == 1:
            for a in range(random.randint(1, int(dc[dif]))):
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
            if random.randint(0, 500) == 0:
                typ = 'city'
            else:
                typ = types[random.randint(0,2)]

        # spawn npc's randomly and populate this list.
        npc = []
        pos = (x, y)
        # If you're not in a city, then create some NPC's
        if typ != 'city' and random.randint(0, 5)//dc[dif] > 0:
            for a in range(random.randint(0, 4)):
                npc.append(NPC(pos))

        # If this is the very first node of the game
        if start:
            # Create some basic enemies
            enemies = [Enemy(dc[dif], [x,y]) for a in range(4)]
            for i in range(len(enemies)):
                # Iterate and make the enemies super weak, to ensure the player doesn't die
                enemies[i].hp = 2+random.randint(0, 5)
                enemies[i].attack = 3+random.randint(0, 3)
            # Create thee story-based NPCs
            npc = [NPC(pos, True) for a in range(3)]
            town = Quest_Town(True, True, True, True, enemies, npc, [])
            # Set the town name
            town.town_name = 'Little Ivywood'
            return town

        # Possibly spawn a quest town for the storyline if they haven't all spawned
        if random.randint(0,300) == 77 and len(self.used_names) < len(open('config/towns.txt').read().split('\n')):
            # Spawn lots of enemies
            enemies = [Enemy(dc[dif], [x,y]) for a in range(random.randint(3, 5))]
            # If it's an unlucky town, spawn a Demon boss there
            if random.randint(0, 2) != 1:
                enemies.append(Demon(dc[dif], [x,y]))
            # Create several people
            npc = [NPC(pos, True) for a in range(random.randint(2, 4))]
            # Create the node
            node = Quest_Town(True, True, True, True, enemies, npc, self.used_names)
            # Add the towns name to the used names
            self.used_names.append(node.town_name)
            return node

        # Return the generated Area_Node object
        return Area_Node(hasNorth, hasSouth, hasEast, hasWest, enemies, typ, npc)

    def spawn_endgame(self, pos):
        '''
        Spawn the endgame lair of Strevras Rane
        '''
        chunk_pos = [a//10 for a in pos]
        # Get a random nearby chunk coordinates
        x = random.randint(chunk_pos[0]-5, chunk_pos[0]+5)*10
        y = random.randint(chunk_pos[1]-5, chunk_pos[1]+5)*10
        # Get a random node within the chunk
        x2 = random.randint(0, 9)
        y2 = random.randint(0, 9)
        # Keep doing the above until the randomly selected node is not the current one
        while self.get_node(x+x2, y+y2) == self.get_node(*pos):
            x = random.randint(chunk_pos[0]-5, chunk_pos[0]+5)*10
            y = random.randint(chunk_pos[1]-5, chunk_pos[1]+5)*10
            x2 = random.randint(0, 9)
            y2 = random.randint(0, 9)
        # Set the selected node as an end area
        self.chunk_array[y//10][x//10].array[y2][x2] = End_Area([x+x2, y+y2])
        # Return an xy coordinate list of the spawned node
        return [x+x2, y+y2]

    def set_node(self, pos, **kwargs):
        '''
        Re-set any values associated with a chunk. Uses a kwargs for variable input
        '''
        x,y = pos
        for var in kwargs:
            if var == 'store':
                self.chunk_array[y//10][x//10].array[y%10][x%10].store = kwargs['store']

    def get_node(self, x, y):
        '''
        Get a node at the given world coordinates
        '''
        # Grab the chunk at the specified position
        chunk = self.chunk_array[y//10][x//10]
        # If the chunk hasn't been generated or loaded
        if not chunk:
            # If the world is a loaded world (not new)
            if self.is_loading:
                # Generate a chunk by it's save string and set it into the map
                chunk = Chunk.get_by_string([y//10, x//10], eval(self.details[y//10][x//10]), self)
                if chunk:
                    # If the get_by_string returned a valid chunk object then add it to the array
                    self.chunk_array[y//10][x//10] = chunk
                else:
                    # Or if it returned 0 then create a chunk for the array
                    self.chunk_array[y//10][x//10] = self.make_chunk(x//10,y//10,'medium',2)
            else:
                # Generate a fresh chunk and set it into the map
                self.chunk_array[y//10][x//10] = self.make_chunk(x//10,y//10,'medium',2)
        # Return the chosen node from the chunk
        return self.chunk_array[y//10][x//10].array[y%10][x%10]

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
            # If the string it's returning is a complete chunk string then load it
            for i, row in enumerate(details):
                for j, node in enumerate(row):
                    # Add a loaded node to the array
                    if node.split('/')[2] == 'town':
                        chunk.array[i][j] = Quest_Town.get_by_string(node)
                    elif node.split('/')[2] == 'lair':
                        chunk.array[i][j] = End_Area()
                    else:
                        chunk.array[i][j] = Area_Node.get_by_string(node)
        else:
            # Otherwise, return 0
            chunk = 0

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
        return self.pos[1] == 99

    def is_far_north(self):
        '''
        Determine if the chunk is on the northern edge of the world
        '''
        return self.pos[1] == 0

    def is_far_east(self):
        '''
        Determine if the chunk is on the eastern edge of the world
        '''
        return self.pos[0] == 99

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
        with open('config/desc.txt') as f:
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
        elif len(self.npc) > 1:
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

class Quest_Town(Area_Node):
    def __init__(self,n,s,e,w,enemies, npc, used_names=[], town_name=None):
        super().__init__(n,s,e,w,enemies,'town',npc)
        self._npc = list(self.npc)
        self.npc = []
        self.is_cleared = False
        if town_name:
            self.town_name = town_name
        else:
            names = open('config/towns.txt').read().split('\n')
            names = [a for a in names if a not in used_names]
            if len(names)-1 == 0:
                self.town_name = 'Random name'
                return
            self.town_name = names[random.randint(0, len(names)-1)]

    def get_description(self):
        '''
        Get the description of the town
        '''
        if len(self.enemies) == 0:
            self.is_cleared = True
        if self.is_cleared:
            self.npc = list(self._npc)
        string = ''
        d2 = {'North':self.hasNorth, 'South':self.hasSouth, 'East':self.hasEast, 'West':self.hasWest}
        # Get the passage description based on the movable directions
        if all([d2[a] for a in d2]):
            string += '\nThere are roads in all directions.'
        else:
            for a in d2:
                if d2[a]:
                    # If the direction is travelable (?) then add the notification to the description string
                    if string and string[-1] not in ('.', '\n'):
                        string += ', another leads to the {}.'.format(a)
                        continue
                    string += '\nA road leads to the {}'.format(a)
        string += '\n'

        if len(self.npc) == 1:
            # If there's one person nearby then tell the player that
            string += '\nA single person stands nearby. They seem to be waiting for someone.'
        elif len(self.npc) > 1:
            # If there's a few then tell the player that there is a group
            string += '\nA group of people mill about nearby. They seem greatly bored, but relieved.'

        if len(self.enemies) > 3:
            # If there are lots of enemies then tell the player that they are in trouble!
            string += '\nYou are surrounded by enemies!'
        else:
            # Otherwise just state the number of enemies.
            string += ('\nThere '+('are {} enemies' if len(self.enemies) != 1 else 'is {} enemy')+' nearby.').format(len(self.enemies))

        if self.is_cleared:
            # If the town has been cleared out then tell the user
            return 'People bustle around the small town of {}, relieved that you helped free them from Rane\'s monsters'.format(self.town_name)+string
        else:
            # Otherwise narrate the level of devastation being wreaked by the monsters
            return 'You are in {}. Monsters run around the town, destroying the houses of the people.'.format(self.town_name)+string

    def __str__(self):
        '''
        Get the save string used in the save file.
        '''
        x = super().__str__()
        x += '/'+self.town_name+'/'+str(int(self.is_cleared))
        return x

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
        typ = 'town'
        npc = [NPC.get_by_string(a) for a in eval(string[2])]
        node = Quest_Town(n, s, e, w, enemies, npc, town_name=string[3])
        node.is_cleared = bool(int(string[4]))
        return node

class End_Area(Area_Node):
    def __init__(self, pos):
        super().__init__(True, True, True, True, [Rane(pos)], 'lair', [])

    def get_description(self):
        '''
        Return the description of the area
        '''
        if self.enemies:
            return 'A large cavern opens before you as the Demon Eyes fuse together, and begin to emanate a dark energy.\nThe warlock, Strevras Rane stands at the far end, facing you.'
        return 'You are in a large rocky cavern.\nStrevras Rane has been defeated, his energy no longer radiates from here.'
