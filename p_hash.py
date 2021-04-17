import pickle, os, cv2, imagehash
from PIL import Image
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import date, datetime

import scryfall_client as Scryfall
import fetch_data as fetch
import utils
from utils import Singleton
from task_executor import TaskExecutor
from config import Config

class Card:
    '''
    Class for mtg card data
    '''
    def __init__(self, id=None, name='', set='', collector_number=None, img_url='', save_img=False):
        self.id = id
        self.name = name
        self.set = set
        self.collector_number = collector_number
        self.img_url = img_url
        self.save_img = save_img
        self.img = None
        self.phash_obj = None

    def get_card_image(self, verbose=False):
        '''
        Use `Scryfall.fetch_card_img()` to get the card image.\n
        `verbose` will be passed to `Scryfall.fetch_card_img()`
        '''
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

    def get_phash(self, hash_size=32, highfreq_factor=4, flatten_phash=True, verbose=False):
        '''
        Calculate the card's pHash value.\n
        `verbose` will be passed to `Scryfall.fetch_card_img()`
        '''
        if self.phash_obj is None:
            # print(f'calculating pHash for {self.name}')
            try:
                img = self.get_card_image(verbose)
                self.phash_obj = _pHash.img_to_phash(img, grayscale=True)
            except AttributeError as err:
                # print helpful message in case of error
                print(f'error with: {self.set}-{self.collector_number}-{self.name.lower().replace(" ", "_")}') #DEBUG
                print('img_url: ', self.img_url)
                print(err)
                # exit()
                # raise err
        
        # print(f'{self.name} done')
        if flatten_phash:
            return self.phash_obj.hash.flatten()
        else:
            return self.phash_obj

    def to_dict(self, flatten_phash=True, verbose=False):
        '''
        Helper function for saving the phash values in a dataframe.\n
        `verbose` will be passed to `Scryfall.fetch_card_img()`
        '''

        b_classes,g_classes,r_classes = utils.get_color_class(self.get_card_image(), eps=0)
        return {
            'id': self.id,
            'name': self.name,
            'set': self.set,
            'collector_number': self.collector_number,
            'img_url': self.img_url,
            'phash': self.get_phash(flatten_phash=flatten_phash, verbose=verbose),
            'b_classes': b_classes,
            'g_classes': g_classes,
            'r_classes': r_classes,
        }

################################################################
################################################################

class _pHash(metaclass=Singleton):
    # def __init__(self):
    #     try:
    #         self.phash_df
    #     except (NameError, AttributeError):
    #         self.phash_df = self.get_pHash_df()

    @staticmethod
    def img_to_phash(img, grayscale=True, img_colorspace='BGR', hash_size=32, highfreq_factor=4):
        '''
        Calculate the pHash for `img`, grayscaled.\n
        ---
        `img` cv2 image object.\n
        `hash_size`, `highfreq_factor` are passed to `imagehash.phash()`
        '''
        if img is None:
            return {'hash': np.array(None)}
        
        if grayscale:
            # convert to grayscale
            if img_colorspace.upper() == 'BGR':
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            elif img_colorspace.upper() == 'RGB':
                img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # convert to PIL image
        img = Image.fromarray(img)
        return imagehash.phash(img, hash_size, highfreq_factor)

    @staticmethod
    def calc_pHash_from_df(cards_df, img_type, max_workers, flatten_phash=True, verbose=False):
        '''
        Calculate pHashes of `cards_df` using multi threading.\n
        ---
        `cards_df` pandas dataframe containing cards\n
        `img_type` should be one of `{'border_crop', 'normal', 'png'}`\n
        `max_workers` max amount of workers in the pool\n
        `verbose` will be passed to `Scryfall.fetch_card_img()`
        '''

        def _task(card, img_type, progress_bar, flatten_phash=True, save_imgs=False, verbose=False):
            '''
            Worker function for calculating phash for `cards_df`.\n
            ---
            `img_type` should be one of `{'border_crop', 'normal', 'png'}`\n
            `progress_bar` a tqdm progress bar object\n
            `save_imgs` flag for saving the fetched card images\n
            `verbose` will be passed to `Scryfall.fetch_card_img()`
            '''
            res = []
            card = card.dropna()
            cards = [card]

            if 'card_faces' in card \
                    and 'image_uris' in card['card_faces'][0]:
                # in case of double faced cards
                faces = card['card_faces']
                cards += [card.copy()]
                
                cards[0]['name'] = f"{card['name']} (front)"
                cards[1]['name'] = f"{card['name']} (back)"
                cards[0]['image_uris'] = faces[0]['image_uris']
                cards[1]['image_uris'] = faces[1]['image_uris']

                progress_bar.total += 1
                progress_bar.refresh()
            
            for item in cards:
                c = Card(
                    id = item['id'],
                    name = item['name'],
                    set = item['set'],
                    collector_number = item['collector_number'],
                    img_url = item['image_uris'][img_type],
                    save_img = save_imgs
                )
                res += [ c.to_dict(flatten_phash, verbose) ]
                progress_bar.update(n=1)
            return res

        phash_df = pd.DataFrame(columns=['id', 'set', 'collector_number', 'name', 'img_url', 'phash']) # init an empty df
        task_master = TaskExecutor(max_workers=max_workers) # init task pool
        # futures = []
        concat_flag = False # a flag for changing tqdm from 'phash pipeline' to 'concating results'

        with tqdm(total=len(cards_df), unit='card', unit_scale=True, desc='Working on pHash pipeline', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
            for (_i,card) in cards_df.iterrows():
                # futures += [ task_master.submit(task=_task, save_imgs=True, img_type=img_type, card=card, progress_bar=progress_bar, verbose=verbose) ]
                task_master.submit(task=_task, save_imgs=True, img_type=img_type, card=card, flatten_phash=flatten_phash, progress_bar=progress_bar, verbose=verbose)
            
            for future in task_master.futures:
                res = future.result()
                if not res[0]['phash'].all():
                    phash_df = phash_df.append(res)
                
                if concat_flag==False and progress_bar.n==progress_bar.total:
                    # flip the flag only when the first progress bar is finished
                    # close the first progress bar and start a new one
                    concat_flag = True
                    tot = progress_bar.total
                    progress_bar.n = tot
                    progress_bar.refresh()
                    progress_bar.close()
                    # print('')
                    progress_bar = tqdm(total=tot, unit='card', unit_scale=True, desc='Concating results', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}')
                    progress_bar.update(len(phash_df))
                elif concat_flag:
                    progress_bar.update(1)
            
            progress_bar.n = progress_bar.total
            progress_bar.refresh()

        # phash_df['collector_number'] = phash_df['collector_number'].astype('int')
        phash_df['b_classes'] = phash_df['b_classes'].astype('uint8')
        phash_df['g_classes'] = phash_df['g_classes'].astype('uint8')
        phash_df['r_classes'] = phash_df['r_classes'].astype('uint8')
        return phash_df.reset_index(drop=True)

    def get_pHash_df(self, img_type='border_crop', max_workers=200, flatten_phash=True, verbose=False, update=False):
        '''
        Return a dataframe with pHashes for all the cards in mtg.\n
        ---
        `img_type` should be one of `{'border_crop', 'normal', 'png'}`\n
        `max_workers` max amount of workers in the pool\n
        `verbose` will be passed to `Scryfall.fetch_card_img()`
        '''

        try:
            return self.phash_df
        except (NameError, AttributeError):
            pass

        self.phash_df = None
        subdir = f'{Config.cards_path}/pHash'
        filename = f'{subdir}/{img_type}.pickle'

        if os.path.exists(filename):
            # load the pickle if it already exists
            obj = None
            with open(filename, 'rb') as f_in:
                obj = pickle.load(f_in)
        
            self.phash_df = obj['data'].copy()
            obj_date_y_m_d = obj['date']
            obj_date_d_m_y = datetime.strptime(obj_date_y_m_d, '%Y-%m-%d').strftime('%d-%m-%Y')

            print(f'pHash pickle date: {obj_date_d_m_y}')
            if update:
                cards_df = Scryfall.search(q={'date':'>'+obj_date_y_m_d}) # update pHashes if new cards are available
                # cards_df = fetch.load_all('cards')
                    
                if cards_df is not None and len(cards_df) > 0:
                    cards_df = cards_df.loc[ map(lambda x: x not in self.phash_df['id'].to_list(), cards_df['id'].to_list()) ] # remove cards already in phash_df, keep only new cards
                    
                    if len(cards_df) > 0:
                        update_flag = input(f'There are {len(cards_df)} new cards, would you like to update phash_df? (Y/N): ').lower()
                        while update_flag!='y' and update_flag!='n':
                            update_flag = input().lower()
                        
                        if update_flag == 'y':
                            print(f'\nupdating pHash for {len(cards_df)} cards')
                            res = _pHash.calc_pHash_from_df(cards_df, img_type, max_workers, flatten_phash, verbose)
                            self.phash_df = pd.concat([self.phash_df, res]).reset_index(drop=True)

                            with open(filename, 'wb') as file:
                                obj = {
                                    'date': date.today().strftime("%Y-%m-%d"),
                                    'data': self.phash_df,
                                    # 'data': phash_df,
                                }
                                pickle.dump(obj, file)
                print(f'\npHash df is up to date')
            return self.phash_df
        else:
            # create a new dataframe and calculate the pHashes
            # cards_df = Scryfall.search(literal='q=frame:2003+(color:b or color:w)') #DEBUG
            cards_df = fetch.load_all('cards')
            self.phash_df = _pHash.calc_pHash_from_df(cards_df, img_type, max_workers, flatten_phash, verbose)
        
        # dump `pHash_df` with an appended date
        print(f"dumping to '{filename}'")
        os.makedirs(subdir, exist_ok=True)
        with open(filename, 'wb') as file:
            obj = {
                'date': date.today().strftime("%Y-%m-%d"),
                'data': self.phash_df,
                # 'data': phash_df,
            }
            pickle.dump(obj, file)
        print('done')

        # self.phash_df = phash_df
        return self.phash_df

pHash = _pHash()

################################################################
################################################################

if __name__ == '__main__':
    # phash_df = pHash.get_pHash_df(update=False)
    phash_df = pHash.get_pHash_df(update=True, flatten_phash=True)
    
    # phash_df = pHash.get_pHash_df(max_workers=1, update=True, flatten_phash=True) #DEBUG
    # phash_df = pHash.get_pHash_df(flatten_phash=True)
    # phash_df = pHash.get_pHash_df(flatten_phash=False)