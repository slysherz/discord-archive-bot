import sqlite3
import json


class ArquiveError(Exception):
    pass


class IDNotFound(ArquiveError):
    pass


# Methods to pack, unpack and match tags
class Tags:
    @staticmethod
    def pack(value):
        if not value:
            value = []

        for v in value:
            assert isinstance(v, str)

        return json.dumps(value)

    @staticmethod
    def unpack(value):
        if not value:
            return []

        return json.loads(value)

    @staticmethod
    def match(value, pattern):
        for v in pattern:
            if not v in value:
                return False

        return True


def scrub(table_name):
    return "".join(chr for chr in table_name if chr.isalnum() or chr in ["_"])


class Archive:
    def __init__(self, db_file):
        print("init")

        # Create a connection to the database
        self.db = sqlite3.connect(db_file)
        self._c = self.db.cursor()

        # Initialize all required tables
        self._c.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- each entry has an ID
                link TEXT,                              -- web link
                updates INTEGER DEFAULT 0,              --
                hidden INTEGER DEFAULT 0,               --
                tags TEXT                               -- 
            )
            """
        )

    # Adds a brand new item to the archive
    def add(self, link, tags):
        print("add", link, tags)

        # TODO: Check if link already exists?

        self._c.execute(
            """
            INSERT INTO entries(link, tags) VALUES(?, ?)
            """,
            [link, Tags.pack(tags)],
        )

        self.db.commit()
        return self._c.lastrowid

    # Updates an item in the archive. Changes are made by inserting a new entry and hidding the old
    # one, but nothing ever gets deleted
    def update(self, id, changed):
        print("update", changed)

        fields = ["link", "id", "tags"]
        parameters = []

        if "link" in changed:
            fields[0] = "?"
            parameters.append(changed["link"])

        if "tags" in changed:
            fields[2] = "?"
            parameters.append(Tags.pack(changed["tags"]))

        parameters.append(id)

        if not self.get(id):
            raise IDNotFound("Entry with id(%s) must exist" % id)

        self._c.execute(
            """
            INSERT INTO entries(link, updates, tags) 
            SELECT %s, %s, %s
                FROM entries 
                WHERE id = ?
            """
            % tuple(fields),
            parameters,
        )

        self.db.commit()
        return self._c.lastrowid

    # Retrieves a single entry, if it exists
    def get(self, id, opts=["id", "link", "tags"]):
        print("get", id, opts)

        query = self._c.execute(
            """
            SELECT * FROM entries WHERE id = ?
            """,
            [id],
        ).fetchone()

        if not query:
            return None

        (_, link, _, _, tags) = query
        entry = {"id": id, "link": link, "tags": Tags.unpack(tags)}
        print(entry)
        return tuple(entry[e] for e in opts)

    def __match(self, entry, search_opts):
        for opt in search_opts:
            if opt == "tags" and not Tags.match(
                Tags.unpack(entry["tags"]), search_opts[opt]
            ):
                return False

        return True

    # Retrieves entries that match the required parameters
    def find(self, search_opts, result_opt):
        print("find", search_opts, result_opt)
        result = []

        for (id, link, _, _, tags) in self._c.execute(
            "SELECT * FROM entries WHERE hidden = 0"
        ):
            entry = {"id": id, "link": link, "tags": Tags.unpack(tags)}

            if not self.__match(entry, search_opts):
                continue

            result.append(tuple(entry[e] for e in result_opt))

        return result

