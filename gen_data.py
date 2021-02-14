from dtd import Backgrounds as bg

'''
for yolo annotation we need to create a new .txt for each .jpg in the train set.
the text file will contain a row for each annotation in the image, `{<class-id> <x/X> <y/Y> <w/X> <h/Y>}`

for example, there are two annotations for `a1.jpg` in `a1.txt`:
    3 0.45 0.55 0.29 0.67
    0 0.2 0.83 0.28 0.44

'''

class CardObject:
    def __init__(self, id=None, cardname='', setid='', parent=None, dim=(0,0)):
        self.id = id
        self.cardname = cardname
        self.setid = setid
        self.parent = parent # type(parent) = ImageObject
        
        if parent is None:
            x = dim[0]/2
            y = dim[1]/2
        else:
            x = (dim[0]/parent.dim[0])/2
            y = (dim[1]/parent.dim[1])/2

        self.bounding_box = {
            'x': x, # center x position of the card in relation to it's parent, [1 > x > 0]
            'y': y, # center y position of the card in relation to it's parent, [1 > y > 0]
            'w': dim[0],
            'h': dim[1],
        }

############################################################

class ImageObject:
    def __init__(self, background=None, cards=[], dim=(0,0)):
        self.background = background
        self.cards = cards # type(cards) = CardObject[]
        self.dim = dim # dim = (width,height)
    
    def add_card(self, card):
        card.parent = self
        self.cards += [card]

    def gen_img(self):
        #TODO use cv2 to compose the img and save it to disk
        pass

############################################################

if __name__ == '__main__':
    bg1 = bg.get_random()
    img = ImageObject(bg1)
