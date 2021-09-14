import requests, json

from config import Config
from .utils import get_token, save_token, delete_token

API_ENDPOINT = f'{Config.API_HOSTNAME}/auth'


def check_jwt():
    token = get_token()
    if token:
        url = API_ENDPOINT
        headers = {'Authorization': f'Bearer {token}'}
        res = requests.post(url, headers=headers)
        body = res.json()
        
        if 'username' in body:
            return body['username']
        else:
            # delete token's file if authentication failed
            delete_token()
    return False

def login(username, password, save_jwt=True):
    url = API_ENDPOINT
    body = {
        'username': username,
        'password': password
    }
    
    res = requests.post(url, body)
    body = res.json()
    if 'access-token' in body:
        if save_jwt:
            save_token(body)
        return True
    return False

def register(username, password):
    url = f'{API_ENDPOINT}/users'
    #TODO
    pass
