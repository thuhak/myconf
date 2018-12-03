from collections import UserDict
from collections.abc import Mapping
import logging
import threading
import json
import os
from glob import glob
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_DELETE, IN_CREATE, IN_MODIFY
import time
try:
    import yaml
    ENABLE_YML = True
except:
    ENABLE_YML = False

logger = logging.getLogger(__name__)


class Conf(UserDict, ProcessEvent):
    '''
    common config file loader, load json and yaml file into Conf instance.
    when there is include=subpath in config file, take it as sub config.
    auto update config when config file has been changed. this feature is
    available only on linux platform.
    '''
    def __init__(self, path):
        self.config_file = path
        self.subdir = ''
        self.lock = threading.RLock()
        self.data = {}
        self.load()
        ProcessEvent.__init__(self)
        monitor_worker = threading.Thread(target=self.monitor)
        monitor_worker.setDaemon(True)
        monitor_worker.start()

    def _load(self, path):
        logger.debug('loading {}'.format(path))
        data = {}
        try:
            with open(path) as f:
                if ENABLE_YML and (path.endswith('.yaml') or path.endswith('.yml')):
                    d = f.read()
                    data = yaml.load(d)
                elif path.endswith('.json'):
                    d = f.read()
                    data = json.loads(d)
        except FileNotFoundError:
            logging.error('can not find file {}'.format(path))
        except:
            logger.error('{} can not parse, skipping'.format(path))
        if not isinstance(data, Mapping):
            logger.warning('{} must be dict format'.format(path))
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
                    logging.debug('loading sub conf {}'.format(sub))
                    data.update(self._load(sub))
            self.data.update(data)

    def process_default(self, event):
        '''update data when config file has been changed'''
        conf = event.path
        flag = conf.endswith('.json')
        if ENABLE_YML:
            flag = flag or conf.endswith('.yaml') or conf.endswith('.yml')
        if flag:
            logger.info('config file change, reloading...')
            time.sleep(1)    #bug fix
            self.load()

    def monitor(self):
        '''big brother is watching you'''
        wm = WatchManager()
        main_mask = IN_MODIFY
        sub_mask = IN_DELETE | IN_MODIFY | IN_CREATE
        logger.info('start watching main config: {}'.format(self.config_file))
        wm.add_watch(self.config_file, main_mask)
        logger.info('start watching sub config: {}'.format(self.subdir))
        wm.add_watch(self.subdir, sub_mask, auto_add=True, rec=True)
        notifier = Notifier(wm, self)
        notifier.loop()
        # while True:
        #     notifier.process_events()
        #     if notifier.check_events():
        #         notifier.read_events()
