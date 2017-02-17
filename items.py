class Item:
    def __init__(self, id, quantity):
        self.quantity = quantity
        self.attrs = self.getAttributes(id)
        self.type = self.attrs['type']

    def getAttributes(self, id):
        '''
        Get the attributes of the item with given id
        '''
        a = {}
        #Open the hidden items dictionary and get the attributes from it.
        for line in open(".items.pydc"):
            line = line.strip().split(',')
            if int(line[0]) == id:
                a['name'] = line[1]
                a['type'] = line[2]
                a['h_restore'] = int(line[3])
                a['damage'] = int(line[4])
                a['damage_resist'] = int(line[5])
                return a
        #Raise an error if item id isn't real.
        raise TypeError('Item ID not a valid Item Type!')

    def __str__(self):
        '''
        Create a string to easily list the inventory.
        '''
        return '{} : Quantity - {}'.format(self.attrs['name'], self.quantity)
