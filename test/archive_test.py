import unittest
import archive


class TestArchive(unittest.TestCase):
    def test_archive(self):
        arc = archive.Archive(":memory:")

        link = "https://www.google.com/"
        tags = {"tag1", "tag2"}

        arc.add(name="name", link=link, tags=tags)

        self.assertEqual((link, tags), arc.get(1, ["link", "tags"]))

        new_tag = {"new tag1", "new tag2"}
        arc.update(1, {"tags": new_tag})

        self.assertEqual((new_tag,), arc.get(2, ["tags"]))

        # Broken links are not allowed
        self.assertRaises(Exception, arc.add, link="broken link")

        # Complex update
        arc.update(
            2,
            {
                "tags": {"add": ["tag3", "tag4"], "sub": ["new tag1"]},
                "name": ["new name"],
            },
        )

        result = arc.get(3, ["name", "tags"])
        self.assertEqual(result[0], "new name")

        self.assertEqual(result[1], {"new tag2", "tag4", "tag3"})

    def test_add_get(self):
        arc = archive.Archive(":memory:")

        id1 = arc.add(name="link", link="link.com", tags=["a", "b"])

        assert not "error" in arc.get(id1)

        # Adding repeated tags should save just a single tag
        id2 = arc.add(name="link", link="link.com", tags=["a", "a"])

        # Select just the tags
        self.assertAlmostEqual(arc.get(id2, ["tags"]), ({"a"},))

    def test_find(self):
        arc = archive.Archive(":memory:")

        arc.add(name="link", link="link.com", tags=["atag"])
        arc.add(name="other", link="other", tags=["other"])

        assert len(arc.find({"name": "link"})) == 1
        assert len(arc.find({"link": "link.com"})) == 1
        assert len(arc.find({"tags": ["atag"]})) == 1
        assert len(arc.find({"keyword": "link"})) == 1

