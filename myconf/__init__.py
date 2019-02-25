'''
Common config file loader

require python3.4+

load json and yaml file into Conf instance.
when there is include=subpath in config file, take it as sub config.
auto update when config file has been changed

'''
#author: thuhak.zhou@nio.com
import types
from inspect import signature
from functools import total_ordering
import threading
import os
import time
from glob import glob
from copy import deepcopy
import bisect
import logging
import json
from collections.abc import Mapping

import yaml
import jmespath
try:
    from pyinotify import WatchManager, Notifier, ProcessEvent, IN_DELETE, IN_CREATE, IN_MODIFY
    HAS_INOTIFY = True
except ImportError:
    HAS_INOTIFY = False


__all__ = ['Conf']
__version__ = '1.1.0'

logger = logging.getLogger(__name__)


@total_ordering
class WatchedData:
    __slots__ = ['expression', 'data', 'funcname']

    def __init__(self, expression, data, funcname):
        self.expression = jmespath.compile(expression)
        self.data = data
        self.funcname = funcname

    def __lt__(self, other):
        return self.funcname < other.funcname

    def __eq__(self, other):
        return self.funcname == other.funcname


class ConfMeta(type):
    '''
    regist callback function
    '''
    def __init__(cls, clsname, bases, clsdict):
        super().__init__(clsname, bases, clsdict)
        watched_items = []
        for k,v in clsdict.items():
            if k.startswith('onchange_') and isinstance(v, types.FunctionType):
                sig = signature(v)
                if 'old' not in sig.parameters or 'new' not in sig.parameters:
                    raise KeyError('callback function {} must contains "old" and "new" parameter'.format(k))
                try:
                    expression = sig.parameters['watched_item'].default
                except:
                    raise KeyError('callback function {} must have default value for watched_item'.format(k))
                watcheddata = WatchedData(expression, None, k)
                bisect.insort(watched_items, watcheddata)
        setattr(cls, 'watched_items', watched_items)


class BasicConf(dict, metaclass=ConfMeta):
    '''
    common config file loader, load json and yaml file into Conf instance.
    when there is include=subpath in config file, take it as sub config.
    '''
    def __init__(self, config_file, refresh=True):
        self.config_file = config_file
        self.subdir = ''
        self.lock = threading.Lock()
        self._data = {}
        self.state_table = {}
        self.load(init=True)
        if refresh:
            monitor_worker = threading.Thread(target=self.monitor)
            monitor_worker.setDaemon(True)
            monitor_worker.start()

    def __getitem__(self, item):
        return self._data[item]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return str(self._data)

    def __contains__(self, item):
        return item in self._data

    @staticmethod
    def _otherdata(other):
        if isinstance(other, BasicConf):
            otherdata = other._data
        else:
            otherdata = other
        return otherdata

    def __eq__(self, other):
        otherdata = self._otherdata(other)
        return self._data == otherdata

    def __ne__(self, other):
        otherdata = self._otherdata(other)
        return self._data != otherdata

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def get(self, k, d=None):
        return self._data.get(k, d)

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

    def load(self, init=False):
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
            self._data = data
            for item in self.watched_items:
                old = item.data
                new = item.expression.search(data)
                if old != new:
                    item.data = new
                    if not init:
                        try:
                            getattr(self, item.funcname)(old, new)
                        except Exception as e:
                            logger.error('callback function {} fail, error is {}'.format(item.funcname, str(e)))

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
        def __init__(self, path, refresh=True):
            ProcessEvent.__init__(self)
            BasicConf.__init__(self, path, refresh)

        def process_default(self, event):
            '''update data when config file has been changed'''
            conf = event.pathname
            flag = conf.endswith('.json') or conf.endswith('.yaml') or conf.endswith('.yml')
            if flag:
                logger.info('config file change, reloading...')
                #bug fix
                time.sleep(1)
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
        def __init__(self, path, refresh=True, interval=3):
            self.interval = interval
            BasicConf.__init__(self, path, refresh)

        def monitor(self):
            while True:
                time.sleep(self.interval)
                self.load()