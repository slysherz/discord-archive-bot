import sqlite3
import json
import time
import datetime
import validators


class ArquiveError(Exception):
    pass


class IDNotFound(ArquiveError):
    pass


class Tags:
    def __init__(self):
        pass

    def update(self, old, dif):
        if isinstance(dif, dict):
            tags = set(self.unpack(old))
            add = dif.get("add", [])

            for value in add:
                tags.add(value)

            sub = dif.get("sub", [])
            for value in sub:
                tags.discard(value)

            return self.pack(list(tags))

        return self.pack(dif)

    def pack(self, value):
        if not value:
            value = []

        assert isinstance(value, list), "Tags must be a list of strings"
        for v in value:
            assert isinstance(v, str), "Each tag must be a string"

        return json.dumps(list(value))

    def unpack(self, value):
        if not value:
            return {}

        return json.loads(value)

    def match_all(self, value, tags):
        for v in tags:
            if not v in value:
                return False

        return True

    def match_any(self, value, tags):
        for v in tags:
            if v in value:
                return True

        return False

    def match(self, value, pattern):
        if isinstance(pattern, dict):
            yes = pattern.get("add", [])
            no = pattern.get("sub", [])

            return self.match_all(value, yes) and not self.match_any(value, no)

        return self.match_all(value, pattern)


class Files:
    def __init__(self, connection):
        self.con = connection

        self.con.execute(
            """
            CREATE TABLE IF NOT EXISTS files(
                id INTEGER PRIMARY KEY AUTOINCREMENT,   
                name TEXT,                              -- name of the file
                size INT,                               -- file size
                data BLOB                               -- content
            )
            """
        )

    def update(self, old, dif):
        return self.pack(dif)

    def pack(self, value):
        if not value:
            return None

        name, data = value
        assert isinstance(name, str)
        assert isinstance(data, bytes)

        size = len(data)

        self.con.execute(
            """
            INSERT INTO files(name, size, data) VALUES(?, ?, ?)
            """,
            [name, size, data],
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
                ctime REAL,                             -- creation time
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
            "ctime": time.ctime,
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
        ctime = time.time()

        if not name and file_id:
            name = fields["file"][0]

        if link:
            link = complete_link(link)

        # TODO: Check if link already exists?

        self.con.execute(
            """
            INSERT INTO entries(name, ctime, tags, link, file) VALUES(?, ?, ?, ?, ?)
            """,
            [name, ctime, tags, link, file_id],
        )

        self.db.commit()
        return self.con.lastrowid

    def delete(self, id, dont_commit=False):
        print("delete", id)

        self.con.execute(
            """
            UPDATE entries
            SET hidden = 1
            WHERE id = ?
            """,
            [id],
        )

        if not dont_commit:
            self.db.commit()

    # Updates an item in the archive. Changes are made by inserting a new entry and hidding the old
    # one, but nothing ever gets deleted
    def update(self, id, changed):
        print("update", changed)

        updateable = ["name", "tags", "link"]
        old_values = self.con.execute(
            """
            SELECT %s FROM entries WHERE id = ?
            """
            % ", ".join(updateable),
            [id],
        ).fetchone()

        if not old_values:
            raise IDNotFound("Entry with id(%s) must exist" % id)

        old = dict(zip(updateable, old_values))

        fields = ["id", "name", "tags", "link"]
        parameters = []

        if "name" in changed:
            fields[1] = "?"
            parameters.append(changed["name"][0])

        if "tags" in changed:
            fields[2] = "?"
            parameters.append(self.tags.update(old["tags"], changed["tags"]))

        if "link" in changed:
            fields[3] = "?"
            parameters.append(complete_link(changed["link"][0]))

        # Used at the end by the WHERE clause
        parameters.append(id)

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

        self.delete(id, True)

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
            if opt == "tags" and not self.tags.match(entry["tags"], search_opts[opt]):
                return False

        return True

    # Retrieves entries that match the required parameters
    def find(self, search_opts, result_opts=None):
        print("find", search_opts, result_opts)

        page = search_opts.get("page", [0])[0]
        assert isinstance(page, int)

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

        # Reverse results order
        result = result[::-1]

        # Use a small slice as the answer
        items_per_page = 10

        page_result = result[items_per_page * page : items_per_page * (page + 1)]
        cols = len(result_opts)
        dots = ["..."] * cols

        if page > 0:
            page_result = [dots, *page_result]

        if len(result) > items_per_page * (page + 1):
            page_result.append(dots)

        return page_result

