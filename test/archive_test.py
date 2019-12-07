import unittest
import archive


class TestArchive(unittest.TestCase):
    def test_archive(self):
        arc = archive.Archive(":memory:")

        link = "some link"
        tags = ["tag1", "tag2"]

        arc.add(link, tags)

        self.assertEqual((link, tags), arc.get(1, ["link", "tags"]))

        new_tag = ["new tag"]
        arc.update(1, {"tags": new_tag})

        self.assertEqual((new_tag,), arc.get(2, ["tags"]))

