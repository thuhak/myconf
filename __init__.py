'''
Common config file loader

require python3.4+

load json and yaml file into Conf instance.
when there is include=subpath in config file, take it as sub config.
auto update when config file has been changed

'''
#author: thuhak.zhou@nio.com
from collections import UserDict
from collections.abc import Mapping
import logging
import threading
import json
import os
import time
from glob import glob
from copy import deepcopy
import yaml

try:
    from pyinotify import WatchManager, Notifier, ProcessEvent, IN_DELETE, IN_CREATE, IN_MODIFY
    HAS_INOTIFY = True
except ImportError:
    HAS_INOTIFY = False



__all__ = ['Conf']
__version__ = '1.1.0'

logger = logging.getLogger(__name__)


class BasicConf(UserDict):
    '''
    common config file loader, load json and yaml file into Conf instance.
    when there is include=subpath in config file, take it as sub config.
    '''
    def __init__(self, path, refresh=True):
        self.config_file = path
        self.subdir = ''
        self.lock = threading.Lock()
        self.data = {}
        self.state_table = {}
        self.load()
        if refresh:
            monitor_worker = threading.Thread(target=self.monitor)
            monitor_worker.setDaemon(True)
            monitor_worker.start()

    def _load(self, path):
        '''load config from path'''
        data = {}
        try:
            if os.stat(path).st_mtime >= self.state_table.get(path, (0,))[0]:
                logger.debug('loading {}'.format(path))
                with open(path) as f:
                    d = f.read()
                    if path.endswith('.yaml') or path.endswith('.yml'):
                        data = yaml.load(d) if d else {}
                    elif path.endswith('.json'):
                        data = json.loads(d) if d else {}
                if not isinstance(data, Mapping):
                    logger.warning('{} must be dict format'.format(path))
                    data = {}
                self.state_table[path] = [time.time(), data]
        except FileNotFoundError:
            logging.error('can not find file {}'.format(path))
        except:
            logger.error('{} can not parse, skipping'.format(path))
        return self.state_table[path][1] if path in self.state_table else {}

    def load(self):
        '''load all config value into instance'''
        with self.lock:
            data = deepcopy(self._load(self.config_file))
            if os.path.isdir(data.get('include', '')):
                self.subdir = data['include']
            elif data and 'include' not in data:
                self.subdir = ''
            if self.subdir:
                sub_confs = glob(os.path.join(self.subdir, '*.json'))
                sub_confs.extend(glob(os.path.join(self.subdir, '*.yml')))
                sub_confs.extend(glob(os.path.join(self.subdir, '*.yaml')))
                for sub in sub_confs:
                    data.update(self._load(sub))
            self.data = data

    def monitor(self):
        raise NotImplemented


if HAS_INOTIFY:
    class Conf(BasicConf, ProcessEvent):
        '''
        common config file loader, load json and yaml file into Conf instance.
        when there is include=subpath in config file, take it as sub config.
        auto update config when config file has been changed. this feature is
        available only on linux platform.
        '''
        def __init__(self, path):
            ProcessEvent.__init__(self)
            BasicConf.__init__(self, path)

        def process_default(self, event):
            '''update data when config file has been changed'''
            conf = event.pathname
            flag = conf.endswith('.json') or conf.endswith('.yaml') or conf.endswith('.yml')
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
            if self.subdir:
                logger.info('start watching sub config: {}'.format(self.subdir))
                wm.add_watch(self.subdir, sub_mask, auto_add=True, rec=True)
            notifier = Notifier(wm, self)
            notifier.loop()

else:
    class Conf(BasicConf):
        '''
        common config file loader, load json and yaml file into Conf instance.
        when there is include=subpath in config file, take it as sub config.
        update data every interval seconds
        '''
        def __init__(self, path, interval=3):
            self.interval = interval
            BasicConf.__init__(self, path)

        def monitor(self):
            while True:
                time.sleep(self.interval)
                self.load()