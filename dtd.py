import os, random, requests, cv2, tarfile
import sys
from tqdm import tqdm
# from glob import glob
# import matplotlib.pyplot as plt

from utils import Singleton
from config import Config

class _Backgrounds(metaclass=Singleton):
    """
    Container class for all background images for generator
    Referenced from geaxgx's playing-card-detection: https://github.com/geaxgx/playing-card-detection
    """
    def __init__(self):
        try:
            self._images # test for existence of `_images`
        except (NameError, AttributeError):
            self._download_url = Config.dtd_download_url
            self._dtd_path = Config.dtd_path
            self._load_dtd() # create & load `_images`
            
            # for dump_name in glob(dumps_dir + '/*.pck'):
            #     with open(dump_name, 'rb') as dump:
            #         print('Loading ' + dump_name)
            #         images = pickle.load(dump)
            #         self._images += images
            # if len(self._images) == 0:
            #     self._images = load_dtd()
            # print('# of images loaded: %d' % len(self._images))

    def get_random(self):
        return random.choice(self._images)

    def _load_dtd(self): #, dump_it=True, dump_batch_size=1000):
        """
        Load Describable Texture Dataset (DTD) from local\n
        ---
        `dtd_path` path of the DTD images folder\n
        ---
        `return` list of all DTD images
        """
        self._images = []
        
        if not os.path.exists(self._dtd_path):
            while True:
                res = input('DTD doesnt exist, would you like to download it? (Y/N): ')
                if res.lower() == 'y':
                    self._download_dtd()
                    break
                elif res.lower() == 'n':
                    exit()

        # file_count = 0
        for (dirpath,_dirnames,files) in os.walk(self._dtd_path):
            files = [ f for f in files if f.endswith('.jpg') ] # choose all jpgs
            if len(files) > 0:
                dirpath = dirpath.replace('\\', '/')
                self._images += [ f'{dirpath}/{f}' for f in files ]
            # file_count += len(files)
        
        # # Search the directory for all images, and append them to a single list
        # with tqdm(unit='file', file=sys.stdout, ascii=False,  unit_scale=True, total=file_count, desc='Loading', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
        #     for subdir in glob(self._dtd_path + "/images/*"):
        #         for f in glob(subdir + "/*.jpg"):
        #             self._images.append(cv2.imread(f))
        #             progress_bar.update(1)
        # print(f"loaded {len(self._images)} images")

        # # Save them as a pickle if necessary
        # if dump_it:
        #     for i in range(math.ceil(len(self._images) / dump_batch_size)):
        #         dump_name = '%s/dtd_dump_%d.pck' % (dtd_path, i)
        #         with open(dump_name, 'wb') as dump:
        #             print('Dumping ' + dump_name)
        #             pickle.dump(self._images[i * dump_batch_size:(i + 1) * dump_batch_size], dump)
        # return self._images

    def _download_dtd(self):
        response = requests.get(self._download_url, stream=True)

        file_size = int(response.headers['content-length'])
        chunk_size = 2**10 #1024
        arcive_path = Config.data_path + '/' + Config.dtd_download_url[Config.dtd_download_url.rfind('/')+1:]

        # download the archive
        if not os.path.exists(arcive_path):
            with tqdm(unit='B', file=sys.stdout, ascii=False, unit_divisor=chunk_size, unit_scale=True, total=file_size, desc='Downloading', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as progress_bar:
                with open(arcive_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size):
                        if chunk: # filter out keep-alive chunks
                            file.write(chunk)
                            progress_bar.update(len(chunk))

        # print('Unpacking file..')
        with tarfile.open(arcive_path) as archive_file:
             for file in tqdm(archive_file.getmembers(), file=sys.stdout, ascii=False, unit='file', unit_scale=True, total=len(archive_file.getmembers()), desc='Unpacking', bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}'):
                # Extract each file to another directory
                archive_file.extract(file, Config.data_path)
        os.remove(arcive_path)

Backgrounds = _Backgrounds()