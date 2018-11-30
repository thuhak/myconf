from collections import UserDict
from collections.abc import Mapping
import logging
import threading
import json
import os
from glob import glob
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_DELETE, IN_CREATE, IN_MODIFY
try:
    import yaml
    ENABLE_YML = True
except:
    ENABLE_YML = False


class Conf(UserDict, ProcessEvent):
    '''
    common config file loader, load json an yaml file into Conf instance.
    when there is include=subpath in config file, take it as sub config.
    auto update config when config file has been changed. this feature is
    available only on linux platform.
    '''
    def __init__(self, path):
        self.config_file = path
        self.subdir = ''
        self.lock = threading.RLock()
        self.load()
        ProcessEvent.__init__(self)
        monitor_worker = threading.Thread(target=self.monitor)
        monitor_worker.setDaemon(True)
        monitor_worker.start()

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
            if isinstance(data, Mapping) and os.path.isdir(data.get('include', '')):
                self.subdir = data['include']
                sub_confs = glob(os.path.join(self.subdir, '*.json'))
                if ENABLE_YML:
                    sub_confs.extend(glob(os.path.join(self.subdir, '*.yml')))
                    sub_confs.extend(glob(os.path.join(self.subdir, '*.yaml')))
                for sub in sub_confs:
                    data.update(self._load(sub))
            self.data = data

    def process_default(self, event):
        '''update when config file has been changed'''
        conf = event.name
        flag = conf.endswith('.json')
        if ENABLE_YML:
            flag = flag or conf.endswith('.yaml') or conf.endswith('.yml')
        if flag:
            logging.info('config file change, reloading...')
            self.load()

    def monitor(self):
        '''big brother is watching you'''
        wm = WatchManager()
        main_mask = IN_MODIFY
        sub_mask = IN_DELETE | IN_MODIFY | IN_CREATE
        logging.info('start watching main config: {}'.format(self.config_file))
        wm.add_watch(self.config_file, main_mask)
        logging.info('start watching sub config: {}'.format(self.subdir))
        wm.add_watch(self.subdir, sub_mask, auto_add=True, rec=True)
        notifier = Notifier(wm, self)
        while True:
            notifier.process_events()
            if notifier.check_events():
                notifier.read_events()
