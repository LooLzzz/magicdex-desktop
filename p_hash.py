import pickle, os
from imagehash import phash
from PIL import Image
import pandas as pd
from tqdm import tqdm
from datetime import date, datetime

import scryfall_client as Scryfall
import fetch_data as fetch
from task_executor import TaskExecutor
from config import Config

class Card:
    def __init__(self, id=None, name='', set='', collector_number=None, img_url='', save_imgs=False):
        self.id = id
        self.name = name
        self.set = set
        self.collector_number = collector_number
        self.img_url = img_url
        self.save_imgs = save_imgs
        # self.img = None
        # self.phash_value = None

    def get_card_image(self, verbose=False):
        c = {
            'id': self.id,
            'name': self.name,
            'set': self.set,
            'collector_number': self.collector_number,
            'img_url': self.img_url
        }
        self.img = fetch.fetch_card_img(c, to_file=self.save_imgs, verbose=verbose)
        return self.img

    def get_phash(self, hash_size=32):
        # print(f'calculating pHash for {self.name}')
        
        img = self.get_card_image()
        img = Image.fromarray(img) # convert to PIL image
        phash_value = phash(img, hash_size)
        
        # print(f'{self.name} done')
        return phash_value

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'set': self.set,
            'collector_number': self.collector_number,
            'phash_value': self.get_phash()
        }

################################################################
################################################################

def task(card, img_type, progress_bar, save_imgs=False):
    res = []
    if 'card_faces' in card \
        and card['card_faces'] is not None \
        and 'image_uris' in card['card_faces'][0]:
        # in case of double faced cards
        
        faces = card['card_faces']
        progress_bar.total += 1
        progress_bar.refresh()
        front = Card(
            id = card['id'],
            name = f"{card['name']} (front)",
            set = card['set'],
            collector_number = card['collector_number'],
            img_url = faces[0]['image_uris'][img_type],
            save_imgs = save_imgs
        )
        back = Card(
            id = card['id'],
            name = f"{card['name']} (back)",
            set = card['set'],
            collector_number = card['collector_number'],
            img_url = faces[1]['image_uris'][img_type],
            save_imgs = save_imgs
        )
        
        res += [ front.to_dict() ]
        progress_bar.update(n=1)
        res += [ back.to_dict() ]
        progress_bar.update(n=1)
    else:
        front = Card(
            id = card['id'],
            name = card['name'],
            set = card['set'],
            collector_number = card['collector_number'],
            img_url = card['image_uris'][img_type],
            save_imgs = save_imgs
        )
        res += [ front.to_dict() ]
        progress_bar.update(n=1)

    return res

def calc_pHash_from_df(cards_df, img_type, max_workers):
    phash_df = pd.DataFrame(columns=['id', 'set', 'collector_number', 'name', 'phash_value'])
    task_master = TaskExecutor(max_workers=max_workers)
    futures = []

    with tqdm(total=len(cards_df), unit='cards', unit_scale=True, desc='Working on pHash pipeline', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
        for (_i,card) in cards_df.iterrows():
            futures += [ task_master.submit(task=task, save_imgs=True, img_type=img_type, card=card, progress_bar=progress_bar) ]
        
        for future in futures:
            res = future.result()
            phash_df = phash_df.append(res)

    return phash_df

# def get_pHash(img_type='normal', max_workers=200):
def get_pHash(img_type='border_crop', max_workers=200):
    phash_df = None
    subdir = f'{Config.cards_path}/pHash'
    filename = f'{subdir}/{img_type}.pickle'

    if os.path.exists(filename):
        obj = None
        with open(filename, 'rb') as f_in:
            obj = pickle.load(f_in)
        
        phash_df = obj['data']
        date_y_m_d = obj['date']
        date_d_m_y = datetime.strptime(date_y_m_d, '%Y-%m-%d').strftime('%d-%m-%Y')

        print(f'pHash pickle date: {date_d_m_y}')
        update_flag = input('would you like to try to update it (y/n)? ').lower()
        while update_flag!='y' and update_flag!='n':
            update_flag = input().lower()
        
        if update_flag == 'y':
            cards_df = Scryfall.search(q={'date':'>'+date_y_m_d}) # update pHashes if more cards are available
            # cards_df = fetch.load_all('cards')
            
            if cards_df is not None and len(cards_df) > 0:
                cards_df = cards_df.loc[ map(lambda x: x not in phash_df['id'].to_list(), cards_df['id'].to_list()) ]
                
                if len(cards_df) > 0:
                    print(f'updating pHash for {len(cards_df)} cards')
                    res = calc_pHash_from_df(cards_df, img_type, max_workers)
                    phash_df = pd.concat([phash_df, res])
                else:
                    print(f'pHash df is up to date')
                    return phash_df
    else:
        cards_df = fetch.load_all('cards')
        phash_df = calc_pHash_from_df(cards_df, img_type, max_workers)
    
    # dump `pHash_df` with an appended date
    subdir = f'{Config.cards_path}/pHash'
    filename = f'{subdir}/{img_type}.pickle'
    os.makedirs(subdir, exist_ok=True)
    
    print(f"dumping to '{filename}'")
    with open(filename, 'wb') as f_out:
        obj = {
            'date': date.today().strftime("%Y-%m-%d"),
            'data': phash_df
        }
        pickle.dump(obj, f_out)
    print('done')

    return phash_df

if __name__ == '__main__':
    phash_df = get_pHash()








    # cards_df = fetch.load_all('cards')
    # # cards_df = Scryfall.search(q={'set':'thb', 't':'basic', 'unique':'prints'})
    # phash_df = pd.DataFrame(columns=['id', 'set', 'collector_number', 'name', 'phash_value'])

    # task_master = TaskExecutor(max_workers=200)
    # futures = []

    # with tqdm(total=len(cards_df), unit='cards', unit_scale=True, desc='Working on pHash pipeline', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
    #     for (_i,card) in cards_df.iterrows():
    #         # futures += [ task_master.submit(task=task, img_type='normal', card=card, progress_bar=progress_bar) ]
    #         futures += [ task_master.submit(task=task, save_imgs=True, img_type='border_crop', card=card, progress_bar=progress_bar) ]
        
    #     for future in futures:
    #         res = future.result()
    #         phash_df = phash_df.append(res)
    #     # progress_bar.n = progress_bar.total
    # # print(phash_df)

    # res = {
    #     'date': date.today().strftime("%Y-%m-%d"),
    #     'data': phash_df
    # }
    
    # subdir = f'{Config.cards_path}/pHash'
    # # filename = f'{subdir}/normal.pickle'
    # filename = f'{subdir}/border_crop.pickle'
    # os.makedirs(subdir, exist_ok=True)
    
    # print(f"dumping to '{filename}'")
    # with open(filename, 'wb') as f_out:
    #     pickle.dump(res, f_out)
    # print('done')

    # with open(filename, 'rb') as f_in:
    #     res = pickle.load(f_in)