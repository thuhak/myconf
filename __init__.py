'''
Common config file loader

load json and yaml file into Conf instance.
when there is include=subpath in config file, take it as sub config.
auto update when config file has been changed

'''
#author: thuhak.zhou@nio.com
try:
    from .inotify_conf import Conf
except:
    from .conf import Conf


__all__ = ['Conf']
__version__ = '1.0.0'
