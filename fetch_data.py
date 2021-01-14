import requests, cv2, os
import pandas as pd
import numpy as np
from scryfall_client import scryfall
from task_queue import TaskQueue
from config import Config
# from IPython.display import display

def get_card_img(card, to_file=False):
    img_url = card.image_uris['normal']
    setid = card['set']
    card_name = card['name'].lower().replace(' ', '-')
    print(f'fetching {setid}_{card_name}...')

    res = requests.get(img_url, stream=True).raw
    img = np.asarray(bytearray(res.read()), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    if to_file:
        dir = f'{Config.card_images_path}'
        os.makedirs(dir, exist_ok=True)
        cv2.imwrite(f'{dir}/{setid}_{card_name}.png', img)
    print(f'{setid}_{card_name} done.')
    return img

def fetch_card_images(cards_df:pd.DataFrame=None, set_id:str=None, num_workers=5): # to_csv=False, csv_name=None):
    if cards_df is None:
        cards_df = scryfall.get_cards_from_set(set_id)

    q = TaskQueue(num_workers, run=True)
    for (_id,card) in cards_df.iterrows():
        q.add_task(get_card_img, card, to_file=True)
    q.join()


#######################################################################################


'''
https://api.scryfall.com/cards/search?order=released&q=oracleid%3Aaa7714b0-2bfb-458a-8ebf-37ec2c53383e&unique=prints
'''