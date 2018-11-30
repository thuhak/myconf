from collections import UserDict
import logging
import threading
import json
import os
from glob import glob
try:
    import yaml
    ENABLE_YML = True
except:
    ENABLE_YML = False


class Conf(UserDict):
    '''
    common config file loader, load json an yaml file into Conf instance.
    when there is include=subpath in config file, take it as sub config.
    '''
    def __init__(self, path):
        self.config_file = path
        self.subdir = ''
        self.lock = threading.RLock()
        self.load()

    def _load(self, path):
        logging.info('loading {}'.format(path))
        try:
            with open(path) as f:
                if ENABLE_YML and path.endswith('.yaml') or path.endswith('.yml'):
                    d = f.read()
                    data = yaml.load(d)
                elif path.endswith('.json'):
                    data = json.load(f)
        except:
            logging.error('{} can not parse'.format(path))
            if path == self.config_file:
                raise ValueError('main config fail')
            else:
                logging.error('sub config fail, skip..')
                return {}
        return data

    def load(self):
        '''load all config value into instance'''
        with self.lock:
            data = self._load(self.config_file)
            if os.path.isdir(data.get('include', '')):
                self.subdir = data['include']
                sub_confs = glob(os.path.join(self.subdir, '*.json'))
                if ENABLE_YML:
                    sub_confs.extend(glob(os.path.join(self.subdir, '*.yml')))
                    sub_confs.extend(glob(os.path.join(self.subdir, '*.yaml')))
                for sub in sub_confs:
                    data.update(self._load(sub))
            self.data = data
