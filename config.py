class Config:
    data_path = './data'
    dtd_path = f'{data_path}/dtd'
    dtd_download_url = 'https://www.robots.ox.ac.uk/~vgg/data/dtd/download/dtd-r1.0.1.tar.gz'
    cards_path = f'{data_path}/cards'
    # card_images_path = f'{data_path}/images'
    # card_images_path = f'{data_path}/images/cards'

    digital_sets = ['akr', 'anb', 'ana', 'oana', 'xana', 'past', 'td2', 'pmic', 'ha1',
                    'ha2', 'ha3', 'ajmp', 'klr', 'pz1', 'pana', 'psdg', 'pmoa', 'prm',
                    'td0', 'me1', 'me2', 'me3', 'me4', 'tpr', 'pz2', 'vma']