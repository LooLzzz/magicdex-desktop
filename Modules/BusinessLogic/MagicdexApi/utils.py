import os, json

from config import Config
from ..utils import Singleton

TOKEN_PATH = os.path.join(Config.documents_path, 'access-token.json')


class AccessToken(metaclass=Singleton):
    @classmethod
    def get_token(cls):
        value = getattr(cls(), '_token', None)
        if value is None and os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'r') as fp:
                obj = json.load(fp)
                cls()._token = value \
                        = obj['access-token'] if 'access-token' in obj else None
        return value
    
    @classmethod
    def set_token(cls, value):
        cls()._token = value

    @classmethod
    def clear_token(cls):
        try:
            cls()._token = None
            if os.path.exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)
            return True
        except:
            return False

TOKEN = AccessToken()


def get_token():
    '''
    Get access token located in `{Config.documents_path}/access-token.json`
    
    :return: Dictionary containing the access token information. None if file not found.
    '''
    return TOKEN.get_token()

def save_token(token:dict):
    try:
        os.makedirs(Config.documents_path, exist_ok=True)
        with open(TOKEN_PATH, 'w') as fp:
            json.dump(token, fp)
        TOKEN.get_token()
        return True
    except:
        return False

def delete_token():
    '''
    delete token file, located in: `{Config.documents_path}/access-token.json`
    '''
    try:
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)
        return TOKEN.clear_token()
    except:
        return False

def add_headers(func):
    def wrapper(*args, **kwargs):
        headers = {
            'Authorization': f'Bearer {TOKEN.get_token()}',
            # 'Content-Type': 'application/json'
        }
        return func(*args, headers=headers, **kwargs)
    return wrapper
