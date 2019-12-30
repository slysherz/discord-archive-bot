import grammar


def flatten(lst):
    flat_list = []
    for sublist in lst:
        if isinstance(sublist, list):
            for item in sublist:
                flat_list.append(item)
        else:
            flat_list.append(sublist)

    return flat_list


def group_opts(args):
    return dict(e for e in args if isinstance(e, tuple))


def free_opts(args):
    return [e for e in args if not isinstance(e, tuple)]


def group_args(args):
    # items to add
    add = []

    # items to remove
    sub = []

    # forget the old value and use this instead
    eq = []

    def insert(lst, items):
        if isinstance(items, list):
            for item in items:
                lst.append(item)

        else:
            lst.append(items)

    for item in args:
        if isinstance(item, grammar.Add):
            insert(add, item.value)

        elif isinstance(item, grammar.Sub):
            insert(sub, item.value)

        else:
            insert(eq, item)

    if eq and (add or sub):
        add += eq
        eq = []

    if eq:
        return eq

    return {"add": add, "sub": sub}


def single_arg(args):
    result = {}

    for key in args:
        if key == "file":
            result[key] = args[key]

        elif key == "link":
            assert isinstance(args[key], str)
            result[key] = args[key]

        elif key == "tags":
            result[key] = flatten(args[key])

        elif key == "name":
            assert len(args[key]) == 1
            result[key] = args[key][0]

        else:
            assert False, "Missing handler for %s" % key

    return result


def map_table(keys, values, map_fn):
    result = []
    for entry in values:
        e = []
        for key, value in zip(keys, entry):
            if key in map_fn:
                value = map_fn[key](value)

            e.append(value)

        result.append(tuple(e))

    return result


class ArchiveBot:
    def __init__(self, archive):
        self.arc = archive

    def _display_tags(self, tags):
        tags = sorted(tags)

        tags_max_size = 100
        txt = ", ".join(tags)

        if len(txt) > tags_max_size - 3:
            return txt[0 : tags_max_size - 3] + "..."

        return txt

    def get_resume(self, id):
        keys = ["id", "name", "tags"]

        return dict(zip(keys, self.arc.get(id, keys)))

    def usage(self, command):
        usage = {
            "add": {
                "usage": "add",
                "syntax": "!add [link] [name: ...] [tags: ...]",
                "examples": [
                    '!add "link.com" name: link tags: tag1 tag2',
                    '!add name: somefile tags: ["tag a", "tag b"]',
                ],
                "description": "Saves a new file or link in the archive. To save a file, drag and drop it into discord and write !add in the message.",
            },
            "get": {
                "usage": "get",
                "syntax": "!get id [...fields]",
                "examples": ["!get 123", "!get 123 [tags, name, id]"],
                "description": "Retrieves a previously saved file or link. Use find to search for the id.",
            },
            "update": {
                "usage": "update",
                "syntax": "!update id [link: ...] [name: ...] [tags: ...]",
                "examples": [
                    "!update 123 name: newname tags: [newone, newtwo]",
                    "!update 123 tags: +addthistag -removethistag",
                ],
                "description": "Modifies an existing entry. Can be used to change the name and add or remove tags.",
            },
            "find": {
                "usage": "find",
                "syntax": "!find [...fields] [tags: ...] [page: N]",
                "examples": ["!find [id, name] tags: must_have -cannot page: 2"],
                "description": "Retrieves a list of entries that match the search parameters.",
            },
            "help": {
                "usage": "help",
                "syntax": "!help [command]",
                "examples": ["!help add"],
                "description": "Displays information about how to use each command.",
            },
            "general": {
                "usage": "archive bot",
                "description": "Bot to keep track and organize files and links. You can add, modify, search and retrieve files in the archive.",
                "examples": [
                    "!help add",
                    '!add "link.com" name: link tags: tag1 tag2',
                    "!get 123",
                    "!update 123 tags: +addthistag -removethistag",
                    "!find [id, name] tags: must_have -cannot page: 2",
                ],
                "syntax": '!command [a, list] tags: +add_this -remove_this link: "put complex things inside quotation marks"',
            },
        }

        return usage.get(command, usage["general"])

    def add(self, args, opts, edits):
        if len(args):
            opts["link"] = args[0]

        if not ("link" in opts or "file" in opts):
            return {
                "error": "Entry must contain either a link or a file",
                "edits": edits,
            }

        opts = single_arg(opts)
        id = self.arc.add(opts)

        result = self.get_resume(id)
        result["edits"] = {"type": "add", "generated_id": id}

        # If the type isn't 'add', we're probably replacing an error
        if edits and edits["type"] == "add":
            self.arc.delete(edits["generated_id"])

        return result

    def get(self, args, opts, edits):
        if not args:
            return {"error": "ID field is missing.", "usage": self.usage("get")}

        keys = ["id", "name", "tags", "link", "file"]
        values = self.arc.get(args[0], keys)

        if not values:
            return {"error": "Entry not found"}

        result = dict(zip(keys, values))
        result["edits"] = {"type": "get"}

        return result

    def find(self, args, opts, edits):
        fields = ["id", "name", "link", "tags"]

        opts = {k: group_args(v) for k, v in opts.items()}
        if args:
            opts["keyword"] = args[0]
        # opts = group_args(opts)
        result = self.arc.find(opts, fields)

        # Use a small slice as the answer
        items_per_page = 10
        page = opts.get("page", [1])[0] - 1

        page_result = map_table(
            fields,
            result[items_per_page * page : items_per_page * (page + 1)],
            {"tags": self._display_tags},
        )

        cols = len(fields)
        dots = ["..."] * cols

        if page > 0:
            page_result = [dots, *page_result]

        if len(result) > items_per_page * (page + 1):
            page_result.append(dots)

        return {"table": (page_result, fields), "edits": {"type": "find"}}

    def update(self, args, opts, edits):
        if not args:
            return {
                "error": "ID field is missing.",
                "usage": self.usage("update"),
                "edits": edits,
            }

        opts = {k: group_args(v) for k, v in opts.items()}

        id = self.arc.update(args[0], opts)

        result = self.get_resume(id)
        result["edits"] = {"type": "update", "generated_id": id}

        # If the type isn't 'update', we're probably replacing an error
        if edits and edits["type"] == "update":
            self.arc.delete(edits["generated_id"])

        return result

    def help(self, args, opts, _edits):
        if args:
            return {"usage": self.usage(args[0]), "edits": {"type": "help"}}

        return {"usage": self.usage("general"), "edits": {"type": "help"}}

    def handle_command(self, name, args, extra):
        edits = extra.pop("edits", None)
        free = free_opts(args)
        opts = {**group_opts(args), **extra}

        try:
            return {
                "add": self.add,
                "get": self.get,
                "find": self.find,
                "update": self.update,
                "help": self.help,
            }[name](free, opts, edits)
        except Exception as e:
            return {"error": str(e), "edits": edits}

    def handle_message(self, message, extra):
        try:
            int_tree = grammar.parse(message)
            tree = grammar.transform(int_tree)

            # result = "```%s\n\n%s```" % (int_tree.pretty(), tree)
            return self.handle_command(tree[0], tree[1], extra)

        except grammar.exceptions.LarkError as error:
            print(error)
            return None

