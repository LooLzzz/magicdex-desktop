import os
from os import path

class Config:
    root_path = path.realpath(path.join(__file__, '..'))
    data_path = path.join(root_path, 'data')
    
    dtd_download_url = 'https://www.robots.ox.ac.uk/~vgg/data/dtd/download/dtd-r1.0.1.tar.gz'
    dtd_path = path.join(data_path, 'dtd')
    
    cards_path = path.join(data_path, 'cards')
    card_images_path = path.join(cards_path, 'images')
    
    phash_dir_path = path.join(cards_path, 'pHash')
    phash_default_dataframe = path.join(phash_dir_path, 'border_crop.pickle')
    phash_all_dataframes = os.listdir(phash_dir_path)