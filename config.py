import os

class Config:
    root_path = os.path.realpath(os.path.join(__file__, '..'))
    data_path = os.path.join(root_path, 'data')
    
    dtd_download_url = 'https://www.robots.ox.ac.uk/~vgg/data/dtd/download/dtd-r1.0.1.tar.gz'
    dtd_path = os.path.join(data_path, 'dtd')
    
    cards_path = os.path.join(data_path, 'cards')
    card_images_path = os.path.join(cards_path, 'images')
    
    phash_dir_path = os.path.join(cards_path, 'pHash')
    phash_default_dataframe = os.path.join(phash_dir_path, 'border_crop.pickle')
    phash_all_dataframes = os.listdir(phash_dir_path)