import pickle, os
from imagehash import phash
from PIL import Image
import pandas as pd
# import numpy as np
from tqdm import tqdm
from datetime import date, datetime

import scryfall_client as Scryfall
import fetch_data as fetch
from task_executor import TaskExecutor
from config import Config

class Card:
    def __init__(self, id=None, name='', set='', collector_number=None, img_url='', save_img=False):
        self.id = id
        self.name = name
        self.set = set
        self.collector_number = collector_number
        self.img_url = img_url
        self.save_img = save_img
        self.img = None
        self.phash_value = None

    def get_card_image(self, verbose=False):
        if self.img is not None:
            return self.img
        # else:
        c = {
            'id': self.id,
            'name': self.name,
            'set': self.set,
            'collector_number': self.collector_number,
            'img_url': self.img_url
        }
        self.img = fetch.fetch_card_img(c, to_file=self.save_img, verbose=verbose)
        return self.img

    def get_phash(self, hash_size=32, verbose=False):
        if self.phash_value is not None:
            return self.phash_value
        # else:
        # print(f'calculating pHash for {self.name}')
        
        try:
            img = self.get_card_image(verbose)
            img = Image.fromarray(img) # convert to PIL image
            self.phash_value = phash(img, hash_size)
        except AttributeError as err:
            print(f'error with: {self.set}-{self.collector_number}-{self.name.lower().replace(" ", "_")}') #DEBUG
            print('img_url: ', self.img_url)
            print(err)
            # exit()
            # raise err
        
        # print(f'{self.name} done')
        return self.phash_value

    def to_dict(self, verbose=False):
        return {
            'id': self.id,
            'name': self.name,
            'set': self.set,
            'collector_number': self.collector_number,
            'img_url': self.img_url,
            'phash_value': self.get_phash(verbose=verbose)
        }

################################################################
################################################################

def task(card, img_type, progress_bar, save_imgs=False, verbose=False):
    res = []
    card = card.dropna()
    if 'card_faces' in card \
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
            save_img = save_imgs
        )
        back = Card(
            id = card['id'],
            name = f"{card['name']} (back)",
            set = card['set'],
            collector_number = card['collector_number'],
            img_url = faces[1]['image_uris'][img_type],
            save_img = save_imgs
        )
        
        res += [ front.to_dict(verbose) ]
        progress_bar.update(n=1)
        res += [ back.to_dict(verbose) ]
        progress_bar.update(n=1)
    else:
        front = Card(
            id = card['id'],
            name = card['name'],
            set = card['set'],
            collector_number = card['collector_number'],
            img_url = card['image_uris'][img_type],
            save_img = save_imgs
        )
        res += [ front.to_dict(verbose) ]
        progress_bar.update(n=1)
    return res

def calc_pHash_from_df(cards_df, img_type, max_workers, verbose=False):
    phash_df = pd.DataFrame(columns=['id', 'set', 'collector_number', 'name', 'img_url', 'phash_value'])
    task_master = TaskExecutor(max_workers=max_workers)
    futures = []
    flag = True

    with tqdm(total=len(cards_df), unit='cards', unit_scale=True, desc='Working on pHash pipeline', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
        for (_i,card) in cards_df.iterrows():
            futures += [ task_master.submit(task=task, save_imgs=True, img_type=img_type, card=card, progress_bar=progress_bar, verbose=verbose) ]
        
        for future in futures:
            res = future.result()
            phash_df = phash_df.append(res)
            
            if flag==True and progress_bar.n==progress_bar.total:
                flag = False
                tot = progress_bar.total
                progress_bar.n = tot
                progress_bar.refresh()
                progress_bar.close()
                # print('')
                progress_bar = tqdm(total=tot, unit='cards', unit_scale=True, desc='Concating results', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}')
                progress_bar.update(len(phash_df))
            elif flag == False:
                progress_bar.update(1)
        
        progress_bar.n = progress_bar.total
        progress_bar.refresh()

    return phash_df.reset_index(drop=True)

# def get_pHash(img_type='normal', max_workers=200):
def get_pHash_df(img_type='border_crop', max_workers=200, verbose=False):
    phash_df = None
    subdir = f'{Config.cards_path}/pHash'
    filename = f'{subdir}/{img_type}.pickle'

    if os.path.exists(filename):
        obj = None
        with open(filename, 'rb') as f_in:
            obj = pickle.load(f_in)
        
        phash_df = obj['data'] #.reset_index()
        obj_date_y_m_d = obj['date']
        obj_date_d_m_y = datetime.strptime(obj_date_y_m_d, '%Y-%m-%d').strftime('%d-%m-%Y')

        print(f'pHash pickle date: {obj_date_d_m_y}')
        cards_df = Scryfall.search(q={'date':'>'+obj_date_y_m_d}) # update pHashes if new cards are available
        # cards_df = fetch.load_all('cards')
            
        if cards_df is not None and len(cards_df) > 0:
            cards_df = cards_df.loc[ map(lambda x: x not in phash_df['id'].to_list(), cards_df['id'].to_list()) ] # remove cards already in phash_df, keep only new cards
            
            if len(cards_df) > 0:
                update_flag = input(f'There are {len(cards_df)} new cards, would you like to update phash_df? (Y/N): ').lower()
                while update_flag!='y' and update_flag!='n':
                    update_flag = input().lower()
                
                if update_flag == 'y':
                    print(f'\nupdating pHash for {len(cards_df)} cards')
                    res = calc_pHash_from_df(cards_df, img_type, max_workers, verbose)
                    phash_df = pd.concat([phash_df, res]).reset_index()

                    with open(filename, 'wb') as f_out:
                        obj = {
                            'date': date.today().strftime("%Y-%m-%d"),
                            'data': phash_df
                        }
                        pickle.dump(obj, f_out)
                    print(f'\npHash df is up to date')
        return phash_df
    else:
        # cards_df = fetch.load_all('cards')
        cards_df = Scryfall.search(literal='q=frame:2003+(color:b or color:w)') #DEBUG
        phash_df = calc_pHash_from_df(cards_df, img_type, max_workers, verbose)
    
    # dump `pHash_df` with an appended date
    # subdir = f'{Config.cards_path}/pHash'
    # filename = f'{subdir}/{img_type}.pickle'
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
    phash_df = get_pHash_df(max_workers=200)