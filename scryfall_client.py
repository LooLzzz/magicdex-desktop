'''
A wrapper for scryfall's api\n
https://api.scryfall.com
'''

from functools import reduce
import re, requests, os, json #, math, wget, ast
import pandas as pd
from tqdm import tqdm
# import numpy as np
# from IPython.display import display

from config import Config
_base_url = 'https://api.scryfall.com'

def use_api(path:str, literal=None, **kwargs):
    '''
    Freely use scryfall's api at https://api.scryfall.com
    
    ## Input
    `path` - request path/type \n
    `literal` - pass a literal scryfall query string (Optional) \n
    `**kwargs` - enter any valid scryfall fields, for a 'not' operator use '_' \n
    ---
    ## Return
    `pd.DataFrame` or `pd.Series` \n
    ---
    ## Examples
    ```
    Scryfall.use_api('/cards/search/?q=o:"exile target permanent"')
    Scryfall.use_api('/cards/search', q={'o':"exile target permanent"})
    Scryfall.use_api('/cards/search', q={'o':['"exile target permanent"', '"exile target creature"']})
    Scryfall.use_api('/cards/search', literal='q=t:planeswalker')
    Scryfall.use_api('/cards/search', frame=2003, layout='normal', _is='funny')
    Scryfall.use_api('/cards/named', fuzzy='sol r')
    ```
    '''
    def _query_dict_to_string(q):
        '''
        `q` = `dict({'a':[val1,val2],'b':val3})` \n
        returns `str('a:val1+a:val2+b:val3')`
        '''

        # q = {'a': ['val1', 'val2'], 'b': 'val3'}
        res = ''
        for (key,val) in q.items():
            if not isinstance(val, (list, tuple)):
                val = [val]
            
            for v in val:    
                if key == 'date':
                    res += f'{key}{v}+'
                else:
                    res += f'{key}:"{v}"+'
        res = res.strip('+')
        return res
        
    def _gen_full_url():
        _path = path.strip('/?')

        if literal is not None:            
            _literal = literal.strip('/?')
            return f'{_base_url}/{_path}/?{_literal}'
        elif len(kwargs) == 0:
            return f'{_base_url}/{_path}'
        # else:
        url = f"{_base_url}/{_path}/?" # url=`https://api.scryfall.com/{path}/?{...}`

        for (key,val) in kwargs.items():
            # turn dict to something scryfall can understand
            if isinstance(val, dict):
                val = _query_dict_to_string(val)
            
            # replace '_' with '-' for the not operator
            key = re.sub(r'^_', '-', key)
            
            # append to url
            url += f'{key}={val}&'
        url = url.rstrip('&')

        return url
    
    ###############
    ###############

    # try:
    #     i = kwargs.pop('i') #DEBUG
    # except KeyError:
    #     pass
    url = _gen_full_url()
    has_more = True
    res = None

    # get cards dataset as json from query
    with tqdm(total=None, unit='card', unit_scale=True, desc="Requesting", bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
        while has_more:
            response = requests.get(url)
            response.raise_for_status() # will raise for anything other than 1xx or 2xx
            res_json = response.json()
            progress_bar.desc = 'Gathering'
            progress_bar.refresh()

            if res_json['object'] == 'list':
                progress_bar.total = res_json['total_cards'] if 'total_cards' in res_json else len(res_json['data'])
                progress_bar.update(len(res_json['data'])) # update tqdm progress
                
                res_df = pd.DataFrame(res_json['data'])#.set_index('id')
                res = pd.concat([res, res_df]) # append newly fetched rows
                # if i is not None: #DEBUG
                #     print(f'task {i}: {100*len(res)/res_json["total_cards"]:.2f}% : {len(res)}/{res_json["total_cards"]}')
                # res += res_json['data']
                has_more = res_json['has_more']
            else:
                res = pd.DataFrame(pd.Series(res_json)).transpose()
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
        res = pd.DataFrame(res).sort_index(axis=1)
    return res

def search(**kwargs):
    '''
    Send a GET request to `https://api.scryfall.com/cards/search` with kwargs as query\n
    
    ## Return
    The response casted to dataframe/series
    '''
    return use_api('/cards/search', **kwargs)

def get_bulk_data(bulk_type='default_cards', to_file=False, subdir=None, filename='Cards', *args, **kwargs):
    '''
    Get bulk data from scryfall. \n

    ## Input
    `cards_type` should be one of `{'oracle_cards', 'unique_artwork', 'default_cards', 'all_cards', 'rulings', 'all_sets'}`\n
        * if `cards_type` is `None` or `''` then it fallsback to `'default_cards'`\n
        * setting `bulk_type='all_sets'` will result in calling `get_all_sets()` method

    ## Return
    The response casted to dataframe/series
    '''
    if bulk_type==None or bulk_type=='':
        bulk_type = 'default_cards'
    elif bulk_type == 'all_sets':
        return get_all_sets(to_file, subdir, filename, *args, **kwargs)

    print('fetching download url..') #DEBUG
    res = requests.get(f'{_base_url}/bulk-data')
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
    # prune un-needed data
    res_df = prune_df(res_df)

    if to_file:
        to_json(res_df, subdir, filename=filename, *args, **kwargs)
    return res_df

def get_all_sets(to_file=False, subdir=None, filename='sets', *args, **kwargs):
    '''
    get info about all sets in magic.
    return value is the response in dataframe/series form
    '''
    sets_df = use_api('/sets')
    if to_file:
        to_json(sets_df, subdir, filename=filename, *args, **kwargs)
    return sets_df

def get_card_from_id(id):
    url = f'{_base_url}/cards/{id}'
    response = requests.get(url)
    response.raise_for_status() # will raise for anything other than 1xx or 2xx
    
    card = response.json()
    return card

#########################################################################################
#########################################################################################
#########################################################################################

def prune_df(df, en_only=True, no_digital=True):    
    '''
    df is excepted to contain cards
    '''
    # flip cards main image_uris is None by default.
    # the image_uris of its card faces are located in ['card_faces'][0/1]['image_uris']
    # extract image_uris of all flip cards

    def _get_digital_sets():
        df = pd.DataFrame()
        path = f'{Config.cards_path}/all_sets.json'
        if os.path.exists(path):
            df = read_json(path)
        else:
            df = get_all_sets()
        
        set_list = df[ df['digital']==True ]['code'].to_list()
        return set_list

    flips = df[ df['image_uris'].isna() & df['name'].apply(lambda card_name: '//' in card_name) ]
    for i in flips.index:
        df.iloc[i]['image_uris'] = df.iloc[i]['card_faces'][0]['image_uris']
    
    # remove all cards without `image_uris`
    nans = df[ df['image_uris'].isna() ]
    df = df.drop(nans.index)
    # df = df[ df['image_uris'].apply(lambda item: item is not None or reduce(lambda a,b: a != None and b != None, item.values()) ) ]
    
    # keep only english cards
    if en_only:
        df = df[ df['lang'] == 'en' ]

    # remove all digital-only sets
    if no_digital:
        digital_sets = _get_digital_sets()
        df = df[ ~ df['set'].isin(digital_sets) ] # ~ <=> not
    return df

def read_json(path, orient='records', lines=True, *args, **kwargs):
    '''
    Used to load DataFrames full of cards or set info.
    '''
    print(f"loading '{path}'..") #DEBUG
    df = pd.read_json(path, orient=orient, lines=lines, *args, **kwargs)

    return df

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
    if 'image_uris' in df:
        df = prune_df(df, en_only, no_digital)

    os.makedirs(subdir, exist_ok=True)
    return df.to_json(f'{subdir}/{filename}.json', orient=orient, lines=lines, indent=indent, *args, **kwargs)