import os
import pandas as pd
import fetch_data as fetch
from scryfall_client import scryfall
from config import Config

# tasks = [
#     {
#         'scryfall_query': {
#             'q': {
#                 'border': 'black',
#                 'frame': 2015, # newest magic
#                 'layout': 'normal', # no flip,fuze,modal,etc..
#             },
#             '_is': 'funny', # no un-sets
#         },
#         'subdir': 'blackborder_2015_normal',
#         'limit_n': 1,
#     },
#     {
#         'scryfall_query': {
#             'q': {
#                 'border': 'black',
#                 'frame': 2003, # newer magic
#                 'layout': 'normal', # no flip,fuze,modal,etc..
#             },
#             '_is': 'funny', # no un-sets
#         },
#         'subdir': 'blackborder_2003_normal',
#         'limit_n': 1,
#     },
#     {
#         'scryfall_query': {
#             'q': {
#                 'border': 'black',
#                 'frame': 1997, # old magic
#                 'layout': 'normal', # no flip,fuze,modal,etc..
#             },
#             '_is': 'funny', # no un-sets
#         },
#         'subdir': 'blackborder_1997_normal',
#         'limit_n': 1,
#     },
# ]

if __name__ == "__main__":
    # cards_df = fetch.load_all('cards')
    # sets_df = fetch.load_all('sets')

    # download `n` random images from df
    # fetch.fetch_card_images(cards_df, limit_n=50, max_workers=5, delay=0.2)

    # loaded_cards[ loaded_cards['image_uris'].apply(lambda item: item == None ) ]

    # loaded_sets.columns
    # list(loaded_sets[loaded_sets['digital']==True]['code'])


    # q=frame:2015&-is=funny&pretty=true
    scryfall_query = {
        'q': {
            'set': ['m21','m20'],
            'frame': 'legendary',
        },
    }

    res = scryfall.search(**scryfall_query)
    res[['name', 'set', 'image_uris']]