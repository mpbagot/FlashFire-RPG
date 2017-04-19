import random
from effects import *

class Item:
    def __init__(self, id, quantity, cost=None):
        self.quantity = quantity
        if cost:
            self.cost = round(cost)
        self.attrs = self.getAttributes(id)
        self.type = self.attrs['type']

    def getAttributes(self, id):
        '''
        Get the attributes of the item with given id
        '''
        a = {}
        #Open the hidden items dictionary and get the attributes from it.
        items = open('config/items.txt').read().split('\n')[1:]
        for line in items:
            line = line.strip().split(',')
            if line != [''] and line[0] == str(id):
                # print('Getting items attrs for item id', id)
                a['name'] = line[1]
                a['type'] = line[2]
                a['h_restore'] = int(line[3])
                a['damage'] = int(line[4])
                a['damage_resist'] = int(line[5])
                return a
        #Raise an error if item id isn't real.
        # print(id)
        raise TypeError('Item ID not a valid Item Type!')

    @staticmethod
    def get(name):
        '''
        Get the Item ID for an Item with a given name
        '''
        for a in open('config/items.txt').read().split('\n')[1:]:
            # print(a.split(','))
            if a and a.split(',')[1].lower() == name:
                return a.split(',')[0]
        return None

    def __str__(self):
        '''
        Create a string to easily list the inventory.
        '''
        return '{} : Quantity - {}'.format(self.attrs['name'], self.quantity)

class Store:
    def __init__(self, level):
        self.items = self.get_store_items(level)

    def __str__(self):
        '''
        Generate the store inventory from the items
        '''
        stuff = ''
        for i, item in enumerate(self.items):
            stuff += ' • '+Item(*item).attrs['name'] + ' - {} Gold\n'.format(round(item[-1]))
        return 'Store:\n'+stuff

    def get_store_items(self, level):
        '''
        Get the store's inventory based on the player's level
        '''
        items = []
        max_item_id = level+5 if level <= 44 else 49
        avail_items = [a for a in range(1, max_item_id)]
        for a in range(7-level//20):
            item = (avail_items[random.randint(0, max_item_id-2)], 1, round(level*(random.random()*5+0.5)))
            if item[0] not in [a[0] for a in items]:
                items.append(item)
        return items
