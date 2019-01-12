import json
import os
import shutil
import unittest
from satstac import Thing, STACError


testpath = os.path.dirname(__file__)


class Test(unittest.TestCase):

    path = os.path.join(testpath, 'test-thing')
    fname = os.path.join(testpath, 'catalog/catalog.json')

    @classmethod
    def tearDownClass(cls):
        """ Remove test files """
        if os.path.exists(cls.path):
            shutil.rmtree(cls.path)

    def get_thing(self):
        """ Configure testing class """
        with open(self.fname) as f:
            data = json.loads(f.read())
        return Thing(data)

    def test_init(self):
        thing1 = self.get_thing()
        assert(thing1.id == 'stac')
        assert(len(thing1.links()) == 3)
        assert(len(thing1.links('self')) == 1)
        data = thing1.data
        del data['links']
        thing2 = Thing(data)
        assert(thing2.links() == [])
        with self.assertRaises(STACError):
            thing2.save()
        print(thing1)

    def test_open(self):
        thing1 = self.get_thing()
        thing2 = Thing.open(self.fname)
        assert(thing1.id == thing2.id)
        assert(
            os.path.basename(thing1.links()[0]) 
            == os.path.basename(thing2.links()[0])
        )

    def test_open_remote(self):
        thing = Thing.open('https://landsat-stac.s3.amazonaws.com/catalog.json')
        assert(thing.id == 'landsat-stac')
        assert(len(thing.data['links']) == 3)

    def test_open_missing_remote(self):
        with self.assertRaises(STACError):
            thing = Thing.open('https://landsat-stac.s3.amazonaws.com/nosuchcatalog.json')

    def test_thing(self):
        thing = self.get_thing()
        assert('id' in thing.data.keys())
        assert('links' in thing.data.keys())
        del thing.data['links']
        assert('links' not in thing.data.keys())
        assert(thing.links() == [])

    def test_get_links(self):
        thing = Thing.open('https://landsat-stac.s3.amazonaws.com/catalog.json')
        things = [Thing.open(t) for t in thing.links('child')]
        assert('landsat-8-l1' in [t.id for t in things])

    def test_add_link(self):
        thing = self.get_thing()
        thing.add_link('testlink', 'bobloblaw', type='text/plain', title='BobLoblaw')
        assert(len(thing.links()) == 4)
        assert(thing.links('testlink')[0] == 'bobloblaw')

    def test_clean_hierarchy(self):
        thing = self.get_thing()
        thing.add_link('testlink', 'bobloblaw')
        assert(len(thing.links()) == 4)
        thing.clean_hierarchy()
        assert(len(thing.links()) == 1)

    def test_getitem(self):
        thing = self.get_thing()
        assert(thing['some_property'] is None)
    
    def test_save(self):
        thing = Thing.open(self.fname)
        thing.save()
        fout = os.path.join(self.path, 'test-save.json')
        thing.save_as(fout)
        assert(os.path.exists(fout))

    def test_save_remote_with_signed_url(self):
        thing = Thing.open(self.fname)
        thing.save_as('https://landsat-stac.s3.amazonaws.com/test/thing.json')

    def test_save_remote_with_bad_signed_url(self):
        envs = dict(os.environ)
        thing = Thing.open(self.fname)
        os.environ['AWS_BUCKET_REGION'] = 'us-east-1'
        with self.assertRaises(STACError):
            thing.save_as('https://landsat-stac.s3.amazonaws.com/test/thing.json')
        os.environ.clear()
        os.environ.update(envs)

    def test_publish(self):
        thing = self.get_thing()
        fout = os.path.join(self.path, 'test-save.json')
        thing.save_as(fout)
        thing.publish('https://my.cat', root=fout)
        assert(thing.links('self')[0] == 'https://my.cat/test-save.json')

    def test_publish_without_saving(self):
        thing = self.get_thing()
        with self.assertRaises(STACError):
            thing.publish('https://my.cat', root=None)