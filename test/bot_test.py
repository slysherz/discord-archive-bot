import unittest
import archive
import archive_bot


class TestBot(unittest.TestCase):
    def test_bot(self):
        arc = archive.Archive(":memory:")
        bot = archive_bot.ArchiveBot(arc)

        # Add a new entry
        bot.handle_message("!add somelink tags: [a, b, c]", {})
        print(bot.handle_message("!get 1", {}))

        # Update old entry
        bot.handle_message("!update 1 tags: [d]", {})
        print(bot.handle_message("!get 2", {}))

        # Find entries, only the new one exists
        print(bot.handle_message("!find [id, link, tags]", {}))

        # self.assertEqual((new_tag,), arc.get(2, ["tags"]))

    def test_files(self):
        arc = archive.Archive(":memory:")
        bot = archive_bot.ArchiveBot(arc)

        file = ("filename.txt", b"some content here")

        # Send pseudo-file
        bot.handle_message("!add file", {"file": file})

        # Get file
        print(bot.handle_message("!get 1", {}))
