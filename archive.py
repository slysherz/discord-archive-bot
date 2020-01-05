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
            tags = self.unpack(old)
            add = dif.get("add", [])

            for value in add:
                tags.add(value)

            sub = dif.get("sub", [])
            for value in sub:
                tags.discard(value)

            return self.pack(tags)

        return self.pack(dif)

    def pack(self, value):
        if not value:
            value = []

        # assert isinstance(value, list), "Tags must be a list of strings"
        s = set()
        for v in value:
            assert isinstance(v, str), "Each tag must be a string"
            s.add(v)

        return json.dumps(list(s))

    def unpack(self, value):
        if not value:
            return {}

        return set(json.loads(value))

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

        (name, data) = self.con.execute(
            """
            SELECT name, data FROM files WHERE id = ?
            """,
            [id],
        ).fetchone()

        return name, data

    def match(self, value, pattern):
        id = value

        if not id:
            return False

        (name,) = self.con.execute(
            """
            SELECT name FROM files WHERE id = ?
            """,
            [id],
        ).fetchone()

        return pattern in name


class Link:
    def __init__(self):
        pass

    def is_url(self, link):
        return validators.url(link, public=True) == True

    def complete_link(self, link):

        if self.is_url(link):
            return link

        for prefix in [
            "https://",
            "https://www.",
        ]:
            if self.is_url(prefix + link):
                return prefix + link

        assert False, "Not a valid link"

    def pack(self, value):
        if not value:
            return value

        # TODO check if link already exists

        return self.complete_link(value)

    def unpack(self, value):
        return value

    def match(self, value, pattern):
        return value and pattern in value


class Notes:
    def __init__(self, connection):
        self.con = connection

        self.con.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- unique id for each tag
                block_id INTEGER,                       -- id for the tag block
                note TEXT                               -- 
            )
            """
        )

    def next_block_id(self):
        (id,) = self.con.execute("SELECT MAX(block_id) FROM notes").fetchone()

        if not id:
            return 1

        return id + 1

    def pack(self, value):
        if not value:
            return None

        id = self.next_block_id()

        for note in value:
            assert isinstance(note, str)
            self.con.execute(
                """
                INSERT INTO notes(block_id, note) VALUES(?, ?)
                """, [id, note]
            )

        return id

    def unpack(self, value):
        return self.con.execute(
            """
            SELECT id, note FROM notes WHERE block_id = ?
            """, [value]
        ).fetchall()

    # TODO add support for editing notes
    def update(self, _old, dif):
        return self.pack(dif)

    def match(self, value, pattern):
        return value and pattern in value


def scrub(table_name):
    return "".join(chr for chr in table_name if chr.isalnum() or chr in ["_"])


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
                notes INTEGER,                          -- 
                FOREIGN KEY(file) REFERENCES files(id)
                FOREIGN KEY(notes) REFERENCES notes(block_id)
            )
            """
        )

        identity = lambda value: value

        self.files = Files(self.db.cursor())
        self.tags = Tags()
        self.link = Link()
        self.notes = Notes(self.db.cursor())
        self.unpackf = {
            "id": identity,
            "name": identity,
            "ctime": time.ctime,
            "updates": identity,
            "hidden": identity,
            "tags": self.tags.unpack,
            "link": self.link.unpack,
            "file": self.files.unpack,
            "notes": self.notes.unpack
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
    def add(self, name=None, link=None, file=None, tags=None, notes=None):
        # print("add", fields)

        tags = self.tags.pack(tags)
        link = self.link.pack(link)
        file_id = self.files.pack(file)
        notes_id = self.notes.pack(notes)
        ctime = time.time()

        if not name and file_id:
            name = file[0]

        self.con.execute(
            """
            INSERT INTO entries(name, ctime, tags, link, file, notes) VALUES(?, ?, ?, ?, ?, ?)
            """,
            [name, ctime, tags, link, file_id, notes_id],
        )

        self.db.commit()
        return self.con.lastrowid

    # Deletes an item from the archive. The item is still kept, but it won't be visible
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

        updateable = ["name", "tags", "link", "notes"]
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

        fields = ["id", "name", "tags", "link", "notes"]
        parameters = []

        if "name" in changed:
            fields[1] = "?"
            parameters.append(changed["name"][0])

        if "tags" in changed:
            fields[2] = "?"
            parameters.append(self.tags.update(old["tags"], changed["tags"]))

        if "link" in changed:
            fields[3] = "?"
            parameters.append(self.link.pack(changed["link"][0]))

        if "notes" in changed:
            fields[4] = "?"
            parameters.append(self.notes.update(old["notes"], changed["notes"]))

        # Used at the end by the WHERE clause
        parameters.append(id)

        self.con.execute(
            """
            INSERT INTO entries(updates, name, tags, link, notes) 
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

        opts = self.prepare_get(opts, ["id", "name", "tags", "link", "file", "notes"])

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

    # Checks if all entry's properties match their respective search options
    def __match(self, entry, search_opts):
        for opt in search_opts:
            assert opt in ["tags", "link", "keyword", "name", "page"], "Cannot search for %s" % opt

            if opt == "tags" and not self.tags.match(entry["tags"], search_opts[opt]):
                return False

            if opt == "link" and not self.link.match(entry["link"], search_opts[opt]):
                return False

            if opt == "keyword" and not self.__match_any(entry, search_opts[opt]):
                return False

            if opt == "name" and not search_opts[opt] in (entry["name"] or ""):
                return False


        return True

    # Checks if any entry's property matches the given pattern
    def __match_any(self, entry, pattern):
        # if self.tags.match(entry["tags"], [pattern]):
        #     return True

        if self.link.match(entry["link"], pattern):
            return True

        if pattern in (entry["name"] or ""):
            return True

        if self.files.match(entry["file"], pattern):
            return True

        if self.notes.match(entry["notes"], pattern):
            return True

        return False

    # Retrieves entries that match the required parameters
    def find(self, search_opts, result_opts=None):
        print("find", search_opts, result_opts)

        page = search_opts.get("page", [0])[0]
        assert isinstance(page, int)

        result_opts = self.prepare_get(result_opts, ["id", "name", "tags", "link"])

        result = []

        for (id, name, tags, link, file, notes) in self.con.execute(
            "SELECT id, name, tags, link, file, notes FROM entries WHERE hidden = 0"
        ):
            entry = {
                "id": id,
                "name": name,
                "tags": self.tags.unpack(tags),
                "link": self.link.unpack(link),
                "file": file,
                "notes": notes
            }

            if not self.__match(entry, search_opts):
                continue

            result.append(tuple(entry[e] for e in result_opts))

        # Reverse results order
        result = result[::-1]
        return result


