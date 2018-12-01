#author: thuhak.zhou@nio.com
'''
Common config file loader

load json an yaml file into Conf instance.
when there is include=subpath in config file, take it as sub config.
auto update when config file has been changed

'''
try:
    from inotify_conf import Conf
except:
    from conf import Conf


__all__ = ['Conf']


def test():
    import time
    import logging
    logging.basicConfig(level=logging.INFO)
    conf = Conf('config.json')
    while True:
        print(conf)
        time.sleep(1)


if __name__ == '__main__':
    test()
