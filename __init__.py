#author: thuhak.zhou@nio.com
try:
    import pyinotify
    from autochange_conf import Conf
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
