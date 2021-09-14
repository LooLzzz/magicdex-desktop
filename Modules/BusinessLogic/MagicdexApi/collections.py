import os, requests, json
from typing import List

from . import utils # add_headers
from config import Config

API_ENDPOINT = f'{Config.API_HOSTNAME}/collections'
TOKEN_PATH = os.path.join(Config.documents_path, 'access-token.json')


## /collections ##
def get(**kwargs):
    @utils.add_headers
    def _inner(headers):
        url = API_ENDPOINT
        response = requests.get(url, **kwargs, headers=headers)
        return response.json()
    return _inner()

def update_cards(cards:List[dict]=[]):
    @utils.add_headers
    def _inner(cards, headers):
        url = API_ENDPOINT
        data = { 'cards': cards }
        response = requests.post(url, json=data, headers=headers)
        return response.json()
    return _inner(cards=cards)


## /collections/all ##
def get_all(**kwargs):
    @utils.add_headers
    def _inner(headers):
        url = f'{API_ENDPOINT}/all'
        response = requests.get(url, params=kwargs, headers=headers)
        return response.json()
    return _inner()


## /collections/<card_id:str> ##
def get_card_by_id(card_id:str, **kwargs):
    @utils.add_headers
    def _inner(headers):
        url = f'{API_ENDPOINT}/{card_id}'
        response = requests.get(url, params=kwargs, headers=headers)
        return response.json()
    return _inner()
