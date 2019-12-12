import unittest
import archive


class TestArchive(unittest.TestCase):
    def test_archive(self):
        arc = archive.Archive(":memory:")

        link = "https://www.google.com/"
        tags = ["tag1", "tag2"]

        arc.add({"name": "name", "link": link, "tags": tags})

        self.assertEqual((link, tags), arc.get(1, ["link", "tags"]))

        new_tag = ["new tag"]
        arc.update(1, {"tags": new_tag})

        self.assertEqual((new_tag,), arc.get(2, ["tags"]))

        # Broken links are not allowed
        self.assertRaises(Exception, arc.add, {"link": "broken link"})

