import unittest
import archive
import archive_bot

no_extras = {"author": ["none"]}


class TestBot(unittest.TestCase):
    def test_bot(self):
        arc = archive.Archive(":memory:")
        bot = archive_bot.ArchiveBot(arc)

        # Add a new entry
        bot.handle_message("!add somelink tags: [a, b, c]", no_extras)
        print(bot.handle_message("!get 1", no_extras))

        # Update old entry
        bot.handle_message("!update 1 tags: [d]", no_extras)
        print(bot.handle_message("!get 2", no_extras))

        # Find entries, only the new one exists
        print(bot.handle_message("!find", no_extras))

        # Add a bare entry
        assert not "error" in bot.handle_message("!add link", no_extras)

        # Add a complete entry
        assert not "error" in bot.handle_message(
            "!add link name: link tags: [a, b, c] read: someone",
            {"author": ["none"], "file": ("filename.txt", b"some content")},
        )

        assert "error" in bot.handle_message('!add "broken link"', no_extras)

        # self.assertEqual((new_tag,), arc.get(2, ["tags"]))

    def test_files(self):
        arc = archive.Archive(":memory:")
        bot = archive_bot.ArchiveBot(arc)

        file = ("filename.txt", b"some content here")

        # Send pseudo-file
        print(bot.handle_message("!add file", {"file": file}))

        # Get file
        print(bot.handle_message("!get 1", {}))

    def test_update(self):
        arc = archive.Archive(":memory:")
        bot = archive_bot.ArchiveBot(arc)

        bot.handle_message('!add "somelink.com" tags: [a, b]', no_extras)

        assert not "error" in bot.handle_message(
            '!update 1 tags: +[c, d] -e link: "otherlink.com" name: name', no_extras
        )

    def test_find(self):
        arc = archive.Archive(":memory:")
        bot = archive_bot.ArchiveBot(arc)

        # One single complex entry
        tags = ", ".join("somerandomtag" + str(e) for e in range(20))
        bot.handle_message("!add test name: name tags: [%s]" % tags, no_extras)

        # Add a bunch of entries to force multiple pages
        for _ in range(20):
            bot.handle_message("!add test", no_extras)

        assert not "error" in bot.handle_message("!find", no_extras)
        assert not "error" in bot.handle_message("!find page: 1", no_extras)
        assert not "error" in bot.handle_message("!find page: 2", no_extras)
