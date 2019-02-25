import unittest
from myconf import Conf
import logging
from collections.abc import Mapping

logging.basicConfig(level=logging.DEBUG)

class MyConf(Conf):
    def onchange_a(self, old, new, watched_item='foo.bar'):
        logging.info('foo.bar changes from {} to {}'.format(old, new))

    def onchange_b(self, old, new, watched_item='a.b'):
        logging.info('a.b changes from {} to {}'.format(old, new))


class TestConf(unittest.TestCase):

    def setUp(self):
        self.conf = MyConf('testconf/test.yml')

    @unittest.skip('test include')
    def test_cmp(self):
        other = Conf('testconf/test.json', refresh=False)
        self.assertEqual(self.conf, other)

    def test_type(self):
        self.assertTrue(isinstance(self.conf, Mapping))

    @unittest.skip('test include')
    def test_changing(self):
        testdata = self.conf['foo']['bar']
        input('have you changed foo.bar in {} ? \npress any key to continue\n'.format(self.conf.config_file))
        newdata = self.conf['foo']['bar']
        self.assertNotEqual(testdata, newdata)

    def test_include(self):
        testdata = self.conf['a']['b']
        input('have you changed a.b in {} ? \npress any key to continue\n'.format(self.conf.config_file))
        newdata = self.conf['a']['b']
        self.assertNotEqual(testdata, newdata)


if __name__ == '__main__':
    unittest.main()