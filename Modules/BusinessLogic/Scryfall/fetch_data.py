import sys, os, requests, cv2
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
# from IPython.display import display

from . import scryfall_client as Scryfall
from ..task_executor import TaskExecutor
from config import Config

def load_all(df_type:str, to_file=True, *args, **kwargs):
    '''
    `df_kind` should be one of {'cards', 'sets'}
    '''
    df = None
    path = f'{Config.cards_path}/all_{df_type}.json'
    if os.path.exists(path):
        df = Scryfall.read_json(path)
    else:
        # bulk_type = df_kind=='cards' ? 'default_cards' : 'all_sets'
        bulk_type = 'default_cards' if df_type=='cards' else 'all_sets'
        df = Scryfall.get_bulk_data(bulk_type, to_file=to_file, filename=f'all_{df_type}')
    return df

def fetch_card_img(card, to_file=False, verbose=True):
    '''
    `card` should have the following properties: {`set`, `name`, (`collector_number` or `number`), (`image_uris` or `img_url`)}
    '''
    if 'image_uris' in card:
        # img_url = card['image_uris']['large']
        img_url = card['image_uris']['normal']
    else:
        img_url = card['img_url']
    if 'collector_number' in card:
        number = card['collector_number']
    else:
        number = card['number']
    setid = card['set']
    card_name = card['name'] \
                    .lower() \
                    .replace(' ', '_') \
                    .replace('-', '_') \
                    .replace(',', '') \
                    .replace("'", '')
    filename = f'{setid}-{number}-{card_name}'
    subdir = f"{Config.cards_path}/images"
    path = f'{subdir}/{filename}.jpg'

    # get img from local dir
    if os.path.exists(path):
        if verbose:
            print(f"image exists, loading '{filename}'..") #DEBUG
        return cv2.imread(path)
    # else:
    # get img from url
    if verbose:
        print(f"image doesnt exist, fetching '{filename}'..") #DEBUG
    res = requests.get(img_url, stream=True).raw
    img = np.asarray(bytearray(res.read()), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # save it
    if to_file:
        os.makedirs(subdir, exist_ok=True)
        cv2.imwrite(path, img)
    if verbose:
        print(f"'{filename}' done.")
    return img

def fetch_card_images(cards_df:pd.DataFrame, limit_n=None, limit_frac=None, max_workers=5, delay=0.1):#, i=None):
    '''
    Return n card images from `cards_df`.\n
    ---
    `cards_df` cards dataframe\n
    `limit_n:int` (optional) how many cards to pool from `cards_df`\n
    `limit_frac:float[0-1]` (optional) how many cards to pool from `cards_df`\n
    `max_workers` will be passed to TaskExecutor\n
    `delay` will be passed to TaskExecutor
    '''
    if limit_n != None:
        cards_df = cards_df.sample(n=limit_n)
    elif limit_frac != None:
        cards_df = cards_df.sample(frac=limit_frac)

    # setup queue for fetching requested card images
    # added delay to workers as requested by scryfall,
    # https://scryfall.com/docs/api#rate-limits-and-good-citizenship
    task_master = TaskExecutor(max_workers=max_workers, delay=delay)
    futures = []
    for (_i,card) in cards_df.iterrows():
        future = task_master.submit(task=fetch_card_img, card=card, to_file=True)
        futures += [(card['name'], future)]
    
    # get results from futures
    res = []
    for (card_name,future) in futures:
        try:
            res += [future.result()]
        except TypeError as err:
            if 'NoneType' in str(err):
                print(f'#### TypeError(NoneType) while retrieving results from {card_name} ####')
                # print(err)
            else:
                raise err
    return res
    


#######################################################################################


'''
get all prints of a specific card
https://api.scryfall.com/cards/search?q=oracleid:aa7714b0-2bfb-458a-8ebf-37ec2c53383e&unique=prints
https://api.scryfall.com/cards/search?q="sol ring"&unique=prints
## for a fuzzy search drop the "" in the 'q=' 

get all cards from a set
https://api.scryfall.com/cards/search?q=set:m10+lang:en

for layout&frame specific tasks refer to
https://scryfall.com/docs/api/layouts
'''