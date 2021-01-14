import re, os, requests, json, ast
import pandas as pd
from config import Config
# from IPython.display import display

class scryfall:
    _base_url = 'https://api.scryfall.com/'

    @staticmethod
    def use_api(path:str, **params):
        '''
        Freely use scryfall's api at https://api.scryfall.com
        
        ## Input
        `path` - request path/type \n
        `**params` - enter any valid scryfall fields, for 'not' operator use '_' \n
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
        url = scryfall._base_url + path.strip('/') + '?'

        for (k,v) in params.items():
            k = re.sub(r'^_', '-', k) # replace '_' with '-' for the not operator
            url += f'{k}={v}&'
        url = url.strip('&')

        has_more = True
        res = []
        
        # get cards dataset as a json from the query
        while has_more:
            r = requests.get(url)
            res_json = json.loads(r.text)
            if res_json['object'] == 'list':
                res += res_json['data']
                has_more = res_json['has_more']
            else:
                res = res_json
                has_more = False

            if has_more:
                url = res_json['next_page']

        # Convert res into a dataframe/series
        try:
            res = pd.DataFrame(res).set_index('id').sort_index()
            # return a series if only one row in available
            if len(res) == 1:
                res = res.iloc[0]
        except ValueError:
            res = pd.Series(res).sort_index()
        return res

    @staticmethod
    def load_csv_to_pd(path):
        df = pd.read_csv(path, delimiter='|')
        for col in df:
            # is `col` supposed to be a dict
            s = df.iloc[0][col]
            if isinstance(s, str):
                if re.match(r"^{(.+:.+)+}$", s) is not None: 
                    df[col] = df[col].apply(ast.literal_eval) #to dict
                    s = df.iloc[0][col]
        return df

    @staticmethod
    def search(**params):
        return scryfall.use_api('/cards/search', **params)

    @staticmethod
    def get_cards_from_set(set_id:str, **params):
        dir = f'{Config.data_path}/sets'
        if os.path.exists(f'{dir}/{set_id}.csv'):
            return scryfall.load_csv_to_pd(f'{dir}/{set_id}.csv')
            # return pd.read_csv(f'{dir}/{set_id}.csv', delimiter='|')

        params['q'] = f'set:{set_id}'
        df = scryfall.search(**params)
        os.makedirs(dir, exist_ok=True)
        df.to_csv(f'{dir}/{set_id}.csv', sep='|')
        return df