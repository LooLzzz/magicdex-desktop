from functools import reduce
import re, requests, os, json
from numpy.lib.function_base import append #, math, wget, ast
import pandas as pd
from tqdm import tqdm
# import numpy as np
from config import Config
# from IPython.display import display

class scryfall:
    '''
    A wrapper for scryfall's api\n
    https://api.scryfall.com
    '''
    _base_url = 'https://api.scryfall.com'

    @staticmethod
    def use_api(path:str, i=None, **kwargs):
        '''
        Freely use scryfall's api at https://api.scryfall.com
        
        ## Input
        `path` - request path/type \n
        `**kwargs` - enter any valid scryfall fields, for a 'not' operator use '_' \n
        ---
        ## Return
        pd.DataFrame` or `pd.Series` \n
        ---
        ## Examples
        ```
        scryfall.use_api('/cards/search', frame=2003, layout='normal', _is='funny')
        scryfall.use_api('/cards/named', fuzzy='sol r')
        ```
        '''
        def query_dict_to_string(q):
            '''
            `q` = `dict({'a':['val1','val2'],'b':'val3'})` \n
            returns `str('a:val1,val2+b:val3')`
            '''

            # q = {'a':['val1','val2'],'b':'val3'}
            splits = str(q) \
                .strip('}{\'') \
                .replace('\'','') \
                .replace(' ','') \
                .split(',')
            
            count = len(splits)-1
            i = 0
            while i < count:
                if '[' in splits[i]:
                    if ']' in splits[i]:
                        splits[i] = splits[i] \
                            .replace('[', '') \
                            .replace(']', '')
                        i += 1
                    else:
                        # splits[i] = f'{splits[i]},{splits.pop(i+1)}'
                        splits[i] = splits[i] + ',' + splits.pop(i+1)
                        count = len(splits)-1
                else:
                    i += 1
            
            res = reduce(lambda a,b: f'{a}+{b}', splits)
            return res

        def gen_full_url():
            url = f"{scryfall._base_url}/{path.strip('/')}/?" # url=`https://api.scryfall.com/path/?`

            for (key, val) in kwargs.items():
                # turn dict to something scryfall can understand
                if isinstance(val, dict):
                    val = query_dict_to_string(val)
                
                # replace '_' with '-' for the not operator
                key = re.sub(r'^_', '-', key)
                
                # append to url
                url += f'{key}={val}&'
            url = url.rstrip('&')

            return url
        
        #########

        url = gen_full_url()
        has_more = True
        res = None

        # get cards dataset as json from query
        with tqdm(total=None, unit='cards', unit_scale=True, desc='Downloading', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
            while has_more:
                response = requests.get(url)
                response.raise_for_status() # will raise for anything other than 1xx or 2xx
                res_json = response.json()
                progress_bar.total = res_json['total_cards']
                progress_bar.refresh()

                if res_json['object'] == 'list':
                    progress_bar.update(len(res_json['data'])) # update tqdm progress
                    
                    res_df = pd.DataFrame(res_json['data'])#.set_index('id')
                    res = pd.concat([res, res_df]) # append newly fetched rows
                    # if i is not None: #DEBUG
                    #     print(f'task {i}: {100*len(res)/res_json["total_cards"]:.2f}% : {len(res)}/{res_json["total_cards"]}')
                    # res += res_json['data']
                    has_more = res_json['has_more']
                else:
                    res = res_json
                    has_more = False # break

                if has_more:
                    url = res_json['next_page']

        # Convert res into a dataframe/series
        try:
            res = res.sort_index(axis=1)
            # if 'set' in res:
            #     res = res.sort_index(axis=1).sort_values(by=['set','name'])
            # else:
            #     res = res.sort_index(axis=1).sort_values(by=['name'])
            # # return a series if only one row is available
            # if len(res) == 1:
            #     res = res.iloc[0]
        except ValueError:
            res = pd.Series(res).sort_index()
        return res

    @staticmethod
    def search(**kwargs):
        '''
        send a GET request to https://api.scryfall.com/cards/search with kwargs as query\n
        return value is the response in dataframe/series form
        '''
        return scryfall.use_api('/cards/search', **kwargs)

    @staticmethod
    def get_bulk_data(bulk_type='default_cards', to_file=False, subdir=None, filename='Cards', *args, **kwargs):
        '''
        `cards_type` should be one of [`oracle_cards`, `unique_artwork`, `default_cards`, `all_cards`, `rulings`, 'all_sets']\n
          * if `cards_type` is `None` or `''` then it fallsback to `default_cards`\n
          * setting `bulk_type='all_sets'` will result in calling `get_all_sets()` method

        return value is the response in dataframe/series form
        '''
        if bulk_type==None or bulk_type=='':
            bulk_type = 'default_cards'
        elif bulk_type == 'all_sets':
            return scryfall.get_all_sets(to_file, subdir, filename, *args, **kwargs)

        print('fetching download url..') #DEBUG
        res = requests.get(f'{scryfall._base_url}/bulk-data')
        res.raise_for_status()
        res_df = pd.DataFrame(res.json()['data'])

        download_uri = res_df[ res_df['type']==bulk_type ]['download_uri'].values[0]
        download_size = res_df[ res_df['type']==bulk_type ]['compressed_size'].values[0]

        # print('downloading bulk..') #DEBUG
        # download with tqdm progress bar
        res = requests.get(download_uri, stream=True)
        frame = bytearray()
        chunk_size = 2**10 #1024
        with tqdm(unit='B', unit_divisor=chunk_size, leave=True, unit_scale=True, total=download_size, desc='Downloading', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
            progress_bar.leave = True
            for chunk in res.iter_content(chunk_size):
                frame.extend(chunk)
                progress_bar.update(chunk_size)
            progress_bar.n = download_size
            progress_bar.refresh()
        
        print('converting downloaded json to DataFrame..') #DEBUG        
        res_df = pd.DataFrame(json.loads(frame)).sort_index(axis=1)#.set_index('id')
        res_df = scryfall.prune_df(res_df)

        if to_file:
            scryfall.to_json(res_df, subdir, filename=filename, *args, **kwargs)
        return res_df

    @staticmethod
    def get_all_sets(to_file=False, subdir=None, filename='sets', *args, **kwargs):
        '''
        get info about all sets in magic.
        return value is the response in dataframe/series form
        '''
        sets_df = scryfall.use_api('/sets')
        if to_file:
            scryfall.to_json(sets_df, subdir, filename=filename, *args, **kwargs)
        return sets_df

    #################

    @staticmethod
    def prune_df(df, en_only=True, no_digital=True):
        '''
        df is excepted to contain cards
        '''
        # remove all cards without `image_uris`
        nans = df[ df['image_uris'].isna() ].index
        df = df.drop(nans)
        # df = df[ df['image_uris'].apply(lambda item: item is not None or reduce(lambda a,b: a != None and b != None, item.values()) ) ]
        
        # keep only english cards
        if en_only:
            df = df[ df['lang'] == 'en' ]

        # remove all digital only sets
        if no_digital:
            df = df[ df['set'].apply(lambda item: item not in Config.digital_sets) ]
        return df

    @staticmethod
    def read_json(path, orient='records', lines=True, *args, **kwargs):
        '''
        Used to load DataFrames full of cards or set info.
        '''
        print(f"loading '{path}'..") #DEBUG
        df = pd.read_json(path, orient=orient, lines=lines, *args, **kwargs)

        return df

    @staticmethod
    def to_json(df:pd.DataFrame, subdir, filename='cards', orient='records', lines=True, indent=0, no_digital=True, en_only=True, *args, **kwargs):
        '''
        Used to save DataFrames full of cards or set info. \n
        If DF contains cards, then drop all cards without an image and cards that are purely digital.
        '''
        if subdir == None or subdir == '':
            subdir = Config.cards_path
        else:
            subdir = f'{Config.data_path}/{subdir.strip("/")}'
        
        if filename==None or filename=='':
            filename = 'cards'
        else:
            filename = re.sub(r'(\.json)$', '', filename)
        print(f"saving data to '{subdir}/{filename}.json'..") #DEBUG

        # if this is true, then df is a card_df
        if 'set' in df:
            df = scryfall.prune_df(df, en_only, no_digital)

        os.makedirs(subdir, exist_ok=True)
        return df.to_json(f'{subdir}/{filename}.json', orient=orient, lines=lines, indent=indent, *args, **kwargs)