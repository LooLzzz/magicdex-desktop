import re, requests, os, json #, math, wget, ast
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
            `q` = `dict({'a':'val1', 'b':'val2'})` \n
            returns `str('a:val1+b:val2')`
            '''
            res = str(q) \
                .strip('}{\'') \
                .replace('\'','') \
                .replace(' ','') \
                .replace(',','+') 
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
        while has_more:
            response = requests.get(url)
            response.raise_for_status() # will raise for anything other than 1xx or 2xx
            
            # res_json = json.loads(response.text)
            res_json = response.json()
            if res_json['object'] == 'list':
                res_df = pd.DataFrame(res_json['data'])#.set_index('id')
                res = pd.concat([res, res_df])
                if i is not None: #DEBUG
                    print(f'task {i}: {100*len(res)/res_json["total_cards"]:.2f}% : {len(res)}/{res_json["total_cards"]}')
                # res += res_json['data']
                has_more = res_json['has_more']
            else:
                res = res_json
                has_more = False

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
        with tqdm(unit='B', unit_divisor=1024, unit_scale=True, total=download_size, desc='Downloading', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as t:
            for chunk in res.iter_content(1024):
                frame.extend(chunk)
                t.update(1024)
        res_df = pd.DataFrame(json.loads(frame)).sort_index(axis=1)#.set_index('id')

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
    def read_json(path, orient='records', lines=True, no_digital=True, en_only=True, *args, **kwargs):
        '''
        Used to load a df full of cards or set info. \n
        If '`path`.json' contains cards, then drop all cards without an image and cards that are purely digital.
        '''
        print(f"loading '{path}'..") #DEBUG
        df = pd.read_json(path, orient=orient, lines=lines, *args, **kwargs)
        
        # if this is true, then we are loading card_df
        if 'set' in df:
            # remove all cards without `img_uris`
            df[ df['image_uris'].apply(lambda item: item is not None ) ]
            
            # keep only english cards
            if en_only:
                df = df[ df['lang'] == 'en' ]

            # remove all digital only sets
            if no_digital:
                df = df[ df['set'].apply(lambda item: item not in Config.digital_sets) ]

        return df

    @staticmethod
    def to_json(df:pd.DataFrame, subdir, filename='cards', orient='records', lines=True, indent=0, *args, **kwargs):
        '''
        save df as json format.
        a quality of life function.
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
        os.makedirs(subdir, exist_ok=True)
        return df.to_json(f'{subdir}/{filename}.json', orient=orient, lines=lines, indent=indent, *args, **kwargs)