from collections import UserDict
from collections.abc import Mapping
import logging
import threading
import json
import os
import time
from glob import glob
try:
    import yaml
    ENABLE_YML = True
except:
    ENABLE_YML = False

logger = logging.getLogger(__name__)


class Conf(UserDict):
    '''
    common config file loader, load json and yaml file into Conf instance.
    when there is include=subpath in config file, take it as sub config.
    update data every interval seconds
    '''
    def __init__(self, path, interval=3):
        self.config_file = path
        self.subdir = ''
        self.interval = interval
        self.lock = threading.RLock()
        self.load()
        update_worker = threading.Thread(target=self.refresh)
        update_worker.setDaemon(True)
        update_worker.start()

    def _load(self, path):
        logger.info('loading {}'.format(path))
        try:
            with open(path) as f:
                if ENABLE_YML and path.endswith('.yaml') or path.endswith('.yml'):
                    d = f.read()
                    data = yaml.load(d)
                elif path.endswith('.json'):
                    data = json.load(f)
        except:
            logger.error('{} can not parse'.format(path))
            if path == self.config_file:
                raise ValueError('main config fail')
            else:
                logger.error('sub config fail, skip..')
        if not isinstance(data, Mapping):
            logger.warning('{} is not a dict')
            data = {}
        return data

    def load(self):
        '''load all config value into instance'''
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

    def refresh(self):
        while True:
            time.sleep(self.interval)
            self.load()

