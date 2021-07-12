import pickle, os, sys, time, cv2, imagehash
from PIL import Image
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import date, datetime

from config import Config

from . import utils
from .ScryfallApi import scryfall_client as Scryfall
from .ScryfallApi import fetch_data as fetch
from .task_executor import TaskExecutor
from ..Gui.QWorkerThread import QWorkerThread

class _pHash(metaclass=utils.Singleton):
    @staticmethod
    def img_to_phash(img:np.ndarray, input_colorspace='BGR', hash_size=32, highfreq_factor=4, crop_scale=1) -> np.ndarray:
        '''
        Calculate the pHash for `img`, grayscaled.
        Image will be resized internally, new image size is calculated as `hash_size * highfreq_factor`
        
        :param img: image in ndarray format
        :param input_colorspace: img colorspace
        :param hash_size: passed to `imagehash.phash()`
        :param highfreq_factor: passed to `imagehash.phash()`
        :returns: phash value as a flatten binary np.ndarray
        '''
        if img is None:
            return {'hash': np.array(None)}
        
        if crop_scale < 1:
            img = utils.crop_scale_img(img, scale=crop_scale)

        # convert to grayscale
        if input_colorspace.upper() == 'BGR':
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif input_colorspace.upper() == 'RGB':
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # convert to PIL image
        # there is no need to explicitly resize the image since the pHash library does so automatically.
        img = Image.fromarray(img)
        res = imagehash.phash(img, hash_size, highfreq_factor)
        return res.hash.flatten()

    @staticmethod
    def calc_pHash_from_df(cards_df, max_workers, save_imgs=True, verbose=False):
        '''
        Calculate pHashes of card from `cards_df`, fetching card images from the `df['image_uris']['border_crop']` field.

        :param cards_df: a pd.Dataframe containing cards
        :param max_workers: max amount of workers in the pool
        :param verbose: passed to `Scryfall.fetch_card_img()`
        '''

        ##############################
        ##############################
        def _task(card, progress_bar, save_imgs, verbose):
            # res = []
            # card = card.dropna()
            # try:
            #     card['card_id'] = card['id']
            #     card['set_id'] = card['set']
            # except KeyError:
            #     pass
            card['face'] = None
            card['released_at'] = pd.to_datetime(card['released_at'])
            cards = [card]

            if 'card_faces' in card \
                    and card['card_faces'] != None \
                    and not isinstance(card['card_faces'], float) \
                    and 'image_uris' in card['card_faces'][0]:
                try:
                    # type(float) means the value is NAN
                    # in case of double faced cards, split them to two different items
                    faces = card['card_faces']
                    card_name = card['name']
                    cards += [ card.copy() ]
                    
                    # cards[0]['name'] = f"{card_name} (front)"
                    cards[0]['image_uris'] = faces[0]['image_uris']
                    # cards[0]['face'] = 'front'

                    cards[1]['name'] = f"{card_name} (back)"
                    cards[1]['image_uris'] = faces[1]['image_uris']
                    # cards[1]['face'] = 'back'
                except Exception as e:
                    print(e, 'error with: ', card['name'])
                finally:
                    progress_bar.total += 1
                    progress_bar.refresh()
            
            for item in cards:
                img = fetch.fetch_card_img(item, to_file=save_imgs, verbose=verbose)
                (b_classes,g_classes,r_classes) = utils.get_color_class(img, num_of_classes=4, eps=0, color_correction=False)

                item['phash'] = _pHash.img_to_phash(img)
                item['b_classes'] = b_classes[0]
                item['g_classes'] = g_classes[0]
                item['r_classes'] = r_classes[0]
                item['image_url'] = item['image_uris']['border_crop']
                progress_bar.update(n=1)
            
            # vals = [ c.values for c in cards ]
            # cols = cards[0].index
            # return pd.DataFrame(vals, columns=cols)#.rename(columns={'id':'card_id','set':'set_id'})
            return pd.DataFrame(cards)#.rename(columns={'id':'card_id','set':'set_id'})
        ##############################
        ##############################

        cols = ['name', 'card_id', 'collector_number', 'set_name', 'set_id', 'released_at', 'image_url', 'phash', 'b_classes', 'g_classes', 'r_classes']
        # cols = ['name', 'id', 'released_at', 'face', 'image_url', 'phash', 'b_classes', 'g_classes', 'r_classes']
        phash_df = pd.DataFrame(columns=cols) # init an empty df
        # task_master = TaskExecutor(max_workers=1) #DEBUG
        task_master = TaskExecutor(max_workers=max_workers) # init task pool
        concat_flag = False # a flag for changing tqdm from 'phash pipeline' to 'concating results'

        with tqdm(total=len(cards_df), ascii=False, file=sys.stdout, unit='card', unit_scale=True, desc='Working on pHash pipeline', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
            for (_i,card) in cards_df.iterrows():
                # futures += [ task_master.submit(task=_task, save_imgs=True, img_type=img_type, card=card, progress_bar=progress_bar, verbose=verbose) ]
                task_master.submit(task=_task, save_imgs=save_imgs, card=card, progress_bar=progress_bar, verbose=verbose)
            
            for future in task_master.futures:
                task_result:pd.DataFrame = future.result() # blocking
                # if not task_result['phash'].all():
                phash_df = phash_df.append(task_result[cols])
                
                if concat_flag==False and progress_bar.n==progress_bar.total:
                    # flip the flag only when the first progress bar is finished
                    # close the first progress bar and start a new one
                    concat_flag = True
                    tot = progress_bar.total
                    progress_bar.n = tot
                    progress_bar.refresh()
                    progress_bar.close()
                    # print('')
                    progress_bar = tqdm(total=tot, ascii=False, file=sys.stdout, unit='card', unit_scale=True, desc='Concatenating results', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}')
                    progress_bar.update(len(phash_df))
                elif concat_flag:
                    progress_bar.update(1)
            
            progress_bar.n = progress_bar.total
            progress_bar.refresh()
        
        # phash_df = phash_df.drop_duplicates('card_id', keep='first') \
        # phash_df['name'] = phash_df['name'].str.rstrip('(front)(back)')
        phash_df = phash_df \
                .sort_values(by=['name','released_at'], ascending=[True,False]) \
                .reset_index(drop=True)
        return phash_df

    def get_pHash_df(self, max_workers=200, save_imgs=True, verbose=False, update=None):
        '''
        Return a dataframe with pHashes for all cards in mtg history.
        
        :param max_workers: max amount of workers in the pool
        :param verbose: passed to `Scryfall.fetch_card_img()`
        '''

        if not update and hasattr(self, 'phash_df'):
            # return `phash_df` if it is already loaded to memory
            return self.phash_df

        self.phash_df = None
        # img_type = 'border_crop'
        # subdir = os.path.join(Config.cards_path, 'pHash')
        # filename = os.path.join(subdir, f'{img_type}.pickle')
        filepath = Config.phash_default_dataframe

        if os.path.exists(filepath):
            # load the pickle if it already exists
            obj = None
            with open(filepath, 'rb') as f_in:
                obj = pickle.load(file=f_in)
        
            self.phash_df = obj['data'].copy()
            # dupes = self.phash_df.drop_duplicates(subset='name', keep='first', inplace=True)
            obj_date = obj['date']
            # obj_date_d_m_y = datetime.strptime(obj_date, '%Y-%m-%d').strftime('%d-%m-%Y')

            print(f'pHash pickle date: {obj_date} with {len(self.phash_df)} entries')
            up_to_date_flag = False

            if update is None:
                update = input(f'Would you like to try to update phash_df? (Y/N): ').lower()
                while update!='y' and update!='n':
                    update = input().lower()
                update = (update == 'y') # to boolean
            
            if update:
                cards_df = Scryfall.search(q={'date':f'>{obj_date}'}) # update pHashes if new cards are available
                # cards_df = Scryfall.search(q={'date':'>2020-01-01'}) 
                # cards_df = fetch.load_all('cards')
                    
                if cards_df is None or len(cards_df) == 0:
                    up_to_date_flag = True
                else:
                    # remove cards already in phash_df, keep only new cards
                    dfe = pd.merge(self.phash_df, cards_df, how='right', on='card_id', suffixes=['_phash',''], indicator=True)
                    dfe = dfe[dfe['_merge'] == 'right_only'][cards_df.columns]
                    cards_df = dfe

                    if len(cards_df) == 0:
                        up_to_date_flag = True
                    else:
                        print(f'\nupdating pHash for {len(cards_df)} cards')
                        res = _pHash.calc_pHash_from_df(cards_df, max_workers=max_workers, save_imgs=save_imgs, verbose=verbose)
                        self.phash_df = pd.concat([self.phash_df, res])#.reset_index(drop=True)
                        # dupes = self.phash_df.drop_duplicates(keep='first', inplace=True)

                        with open(filepath, 'wb') as file:
                            obj = {
                                'date': date.today().strftime("%Y-%m-%d"),
                                'data': self.phash_df,
                                # 'data': phash_df,
                            }
                            pickle.dump(obj, file)
                        up_to_date_flag = True
                
                if up_to_date_flag:
                    if len(cards_df) == 0:
                        print(f'No new cards are available, pHash df is up to date with {len(self.phash_df)} entries')
                    else:
                        print(f'pHash df is up to date with {len(self.phash_df)} entries')
            
            self.phash_df = self.phash_df \
                .sort_values(by=['name','released_at'], ascending=[True,False]) \
                .reset_index(drop=True)
            return self.phash_df
        else:
            # create a new dataframe and calculate the pHashes
            cards_df = fetch.load_all('cards')
            self.phash_df = _pHash.calc_pHash_from_df(cards_df, max_workers=max_workers, save_imgs=save_imgs, verbose=verbose)
        
        # dump `pHash_df` with an appended date
        print(f"dumping to '{filepath}'")
        os.makedirs(Config.phash_dir_path, exist_ok=True)
        with open(filepath, 'wb') as file:
            obj = {
                'date': date.today().strftime("%Y-%m-%d"),
                'data': self.phash_df,
                # 'data': phash_df,
            }
            pickle.dump(obj, file)
        print('done')

        # self.phash_df = phash_df
        return self.phash_df

    def get_pHash_df_qtasync(self, parent=None, callback=None, max_workers=200, save_imgs=True, verbose=False, update=None):        
        # res = self.get_pHash_df(max_workers=max_workers, save_imgs=save_imgs, verbose=verbose, update=update)
        # callback(res)

        worker = QWorkerThread(parent=parent, task=self.get_pHash_df, max_workers=max_workers, save_imgs=save_imgs, verbose=verbose, update=update)
        worker.finished.connect(worker.deleteLater)
        
        if callback is not None:
            worker.results.connect(callback)

        return worker


pHash = _pHash()

################################################################
################################################################

# if __name__ == '__main__':
#     # phash_df = pHash.get_pHash_df(update=False)
#     phash_df = pHash.get_pHash_df(update=True, flatten_phash=True)
    
#     # phash_df = pHash.get_pHash_df(max_workers=1, update=True, flatten_phash=True) #DEBUG
#     # phash_df = pHash.get_pHash_df(flatten_phash=True)
#     # phash_df = pHash.get_pHash_df(flatten_phash=False)