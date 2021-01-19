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

def load_all_cards():
    cards_df = None
    
    if os.path.exists(f'{Config.cards_path}/all_cards.json'):
        cards_df = scryfall.read_json(f'{Config.cards_path}/all_cards.json')
    else:
        cards_df = scryfall.get_bulk_data('default_cards', to_file=True, filename='all_cards')
    
    return cards_df

def load_all_sets():
    sets_df = None
    
    if os.path.exists(f'{Config.cards_path}/all_sets.json'):
        sets_df = scryfall.read_json(f'{Config.cards_path}/all_sets.json')
    else:
        sets_df = scryfall.get_bulk_data('all_sets', to_file=True, filename='all_sets')
    
    return sets_df

if __name__ == "__main__":
    cards_df = load_all_cards()
    sets_df = load_all_sets()

    # download n random images from df
    fetch.fetch_card_images(cards_df, limit_n=50, max_workers=5, delay=0.2)

    # loaded_cards[ loaded_cards['image_uris'].apply(lambda item: item == None ) ]

    # loaded_sets.columns
    # list(loaded_sets[loaded_sets['digital']==True]['code'])