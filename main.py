import os
import pandas as pd
import fetch_data as fetch
from scryfall_client import scryfall
from config import Config

if __name__ == "__main__":
    cards_df = fetch.load_all('cards')
    sets_df = fetch.load_all('sets')

    # download `n` random images from df
    fetch.fetch_card_images(cards_df, limit_n=50, max_workers=5, delay=0.2)

    # loaded_sets.columns
    # list(loaded_sets[loaded_sets['digital']==True]['code'])


    # 'scryfall_query': {
    #     'q': {
    #         'border': 'black',
    #         'frame': 2015, # newest magic
    #         'layout': 'normal', # no flip,fuze,modal,etc..
    #     },
    #     '_is': 'funny', # no un-sets
    # }
    # scryfall_query = {
    #     'q': {
    #         'set': ['m21','m20'],
    #         'frame': 'legendary',
    #     },
    # }

    # res = scryfall.search(**scryfall_query)
    # res[['name', 'set', 'image_uris']]