import unittest

import priyom.api.sitemap as sitemap

class TestSitemap(unittest.TestCase):
    def test_build_tree(self):
        root = sitemap.Node()
        child1 = sitemap.Node.subnode(root)
        child2 = sitemap.Node.subnode(root)

        self.assertSequenceEqual(
            root,
            [child1, child2])
        self.assertIs(child1.parent, root)
        self.assertIs(child2.parent, root)
        self.assertEqual(len(root), 2)
