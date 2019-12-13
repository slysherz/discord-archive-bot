import sqlite3
import json
import time
import validators


class ArquiveError(Exception):
    pass


class IDNotFound(ArquiveError):
    pass


class Tags:
    def __init__(self):
        pass

    def pack(self, value):
        if not value:
            value = []

        for v in value:
            assert isinstance(v, str)

        return json.dumps(value)

    def unpack(self, value):
        if not value:
            return []

        return json.loads(value)

    def match(self, value, pattern):
        for v in pattern:
            if not v in value:
                return False

        return True


class Files:
    def __init__(self, connection):
        self.con = connection

        self.con.execute(
            """
            CREATE TABLE IF NOT EXISTS files(
                id INTEGER PRIMARY KEY AUTOINCREMENT,   
                name TEXT,                              -- name of the file
                ctime INT,                              -- creation time
                size INT,                               -- file size
                data BLOB                               -- content
            )
            """
        )

    def pack(self, value):
        if not value:
            return None

        name, data = value
        assert isinstance(name, str)
        assert isinstance(data, bytes)

        ctime = int(time.time())
        size = len(data)

        self.con.execute(
            """
            INSERT INTO files(name, ctime, size, data) VALUES(?, ?, ?, ?)
            """,
            [name, ctime, size, data],
        )

        return self.con.lastrowid

    def unpack(self, id):
        if not id:
            return None

        (_, name, _, _, data) = self.con.execute(
            """
            SELECT * FROM files WHERE id = ?
            """,
            [id],
        ).fetchone()

        return name, data


def scrub(table_name):
    return "".join(chr for chr in table_name if chr.isalnum() or chr in ["_"])


def complete_link(link):
    def is_url(link):
        return validators.url(link, public=True) == True

    if is_url(link):
        return link

    for prefix in [
        "https://",
        "https://www.",
    ]:
        if is_url(prefix + link):
            return prefix + link

    assert False, "Not a valid link"


class Archive:
    def __init__(self, db_file):
        print("init")

        # Create a connection to the database
        self.db = sqlite3.connect(db_file)
        self.con = self.db.cursor()

        # Initialize all required tables
        self.con.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- each entry has an ID
                name TEXT,                              --
                updates INTEGER DEFAULT 0,              --
                hidden INTEGER DEFAULT 0,               --
                tags TEXT,                              -- 
                link TEXT,                              -- 
                file INTEGER,                           -- 
                FOREIGN KEY(file) REFERENCES files(id)
            )
            """
        )

        identity = lambda value: value

        self.files = Files(self.db.cursor())
        self.tags = Tags()
        self.unpackf = {
            "id": identity,
            "name": identity,
            "updates": identity,
            "hidden": identity,
            "tags": self.tags.unpack,
            "link": identity,
            "file": self.files.unpack,
        }

    def unpack(self, keys, values):
        return tuple(self.unpackf[key](value) for key, value in zip(keys, values))

    def prepare_get(self, keys, allowed):
        if not keys:
            keys = allowed

        for key in keys:
            assert key in allowed, "Getting key '%s' is not allowed" % key

        return keys

    # Adds a brand new item to the archive
    def add(self, fields):
        print("add", fields)

        name = fields.get("name", None)
        tags = self.tags.pack(fields.get("tags", None))
        link = fields.get("link", None)
        file_id = self.files.pack(fields.get("file", None))

        if link:
            link = complete_link(link)

        # TODO: Check if link already exists?

        self.con.execute(
            """
            INSERT INTO entries(name, tags, link, file) VALUES(?, ?, ?, ?)
            """,
            [name, tags, link, file_id],
        )

        self.db.commit()
        return self.con.lastrowid

    # Updates an item in the archive. Changes are made by inserting a new entry and hidding the old
    # one, but nothing ever gets deleted
    def update(self, id, changed):
        print("update", changed)

        fields = ["id", "name", "tags", "link"]
        parameters = []

        if "name" in changed:
            fields[1] = "?"
            parameters.append(changed["name"])

        if "tags" in changed:
            fields[2] = "?"
            parameters.append(self.tags.pack(changed["tags"]))

        if "link" in changed:
            fields[3] = "?"
            parameters.append(changed["link"])

        # Used at the end by the WHERE clause
        parameters.append(id)

        if not self.get(id):
            raise IDNotFound("Entry with id(%s) must exist" % id)

        self.con.execute(
            """
            INSERT INTO entries(updates, name, tags, link) 
            SELECT %s
                FROM entries 
                WHERE id = ?
            """
            % " ,".join(fields),
            parameters,
        )

        new_id = self.con.lastrowid

        self.con.execute(
            """
            UPDATE entries
            SET hidden = 1
            WHERE id = ?
            """,
            [id],
        )

        self.db.commit()
        return new_id

    # Retrieves a single entry, if it exists
    def get(self, id, opts=None):
        print("get", id, opts)

        opts = self.prepare_get(opts, ["id", "name", "tags", "link", "file"])

        query = self.con.execute(
            """
            SELECT %s FROM entries WHERE id = ?
            """
            % ", ".join(opts),
            [id],
        ).fetchone()

        if not query:
            return None

        return self.unpack(opts, query)

    def __match(self, entry, search_opts):
        for opt in search_opts:
            if opt == "tags" and not self.tags.match(
                self.tags.unpack(entry["tags"]), search_opts[opt]
            ):
                return False

        return True

    # Retrieves entries that match the required parameters
    def find(self, search_opts, result_opts=None):
        print("find", search_opts, result_opts)

        result_opts = self.prepare_get(result_opts, ["id", "name", "tags", "link"])

        result = []

        for (id, name, tags, link) in self.con.execute(
            "SELECT id, name, tags, link FROM entries WHERE hidden = 0"
        ):
            entry = {
                "id": id,
                "name": name,
                "tags": self.tags.unpack(tags),
                "link": link,
            }

            if not self.__match(entry, search_opts):
                continue

            result.append(tuple(entry[e] for e in result_opts))

        return result

