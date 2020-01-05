import grammar

# Flattens a list by one level
def flatten(lst):
    flat_list = []
    for sublist in lst:
        if isinstance(sublist, list):
            for item in sublist:
                flat_list.append(item)
        else:
            flat_list.append(sublist)

    return flat_list


# Separates Add from Sub values
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


# Separates 'normal' tags from key:value tags
def extract_named_tags(tags):
    named_tags = {}
    clear_tags = []
    for tag in tags:
        j = tag.rfind(":")
        if j == -1:
            clear_tags.append(tag)
        else:
            key = tag[:j]
            value = tag[j + 1:]

            if not key in named_tags:
                named_tags[key] = []

            named_tags[key].append(value)

    return clear_tags, named_tags


# Extracts key:value tags into their own column
def unpack_tags_column(keys, values, new_columns=None):
    if not "tags" in keys:
        return keys, values

    i = keys.index("tags")
    temp = []
    if new_columns == None:
        new_columns = set()

        for j in range(len(values)):
            entry = values[j]
            clear_tags, named_tags = extract_named_tags(entry[i])
            new_columns.update(named_tags)
            temp.append((clear_tags, named_tags))

        new_columns = sorted(new_columns)

    keys = [*keys, *new_columns]
    for j in range(len(values)):
        entry = values[j]
        clear_tags, named_tags = temp[j]
        new_values = [named_tags.get(key, None) for key in new_columns]
        
        new_entry = [*entry, *new_values]
        new_entry[i] = clear_tags
        values[j] = new_entry        

    return keys, values


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

    def get_resume(self, id):
        keys = ["id", "name", "tags"]

        keys, values = unpack_tags_column(keys, [self.arc.get(id, keys)])

        return dict(zip(keys, values[0]))

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
                "syntax": "!find [keyword] [tags: ...] [page: N]",
                "examples": ["!find keyword tags: must_have -cannot page: 2"],
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
                    "!find keyword tags: must_have -cannot page: 2",
                ],
                "syntax": '!command [a, list] tags: +add_this -remove_this link: "put complex things inside quotation marks"',
            },
        }

        return usage.get(command, usage["general"])

    def add(self, args, opts, edits):
        arc_opts = {}

        if len(args) and not "link" in opts:
            opts["link"] = args[0]

        tags = ["added_by:%s" % opts["author"][0]]

        for key, value in opts.items():
            if key == "tags":
                arc_opts[key] = flatten(value)
            
            elif key == "file":
                arc_opts[key] = value

            elif key == "link":
                assert isinstance(value[0], str)
                arc_opts[key] = value

            elif key == "tags":
                arc_opts[key] = flatten(args[key])

            elif key == "name":
                assert len(value) == 1
                arc_opts[key] = value[0]

            elif key == "notes":
                arc_opts[key] = flatten(value)

            elif key == "author":
                # Added as a tag, skip
                pass

            else:
                assert len(value) == 1, "Expected a single argument for %s." % key
                val = value[0]
                assert isinstance(val, (str, int)), "Value given to %s must be a string." % key

                tags.append("%s:%s" % (key, val))

        arc_opts["tags"] = [*arc_opts.get("tags", []), *tags]

        if not ("link" in arc_opts or "file" in arc_opts):
            return {
                "error": "Entry must contain either a link or a file",
                "edits": edits,
            }

        id = self.arc.add(**arc_opts)

        result = self.get_resume(id)
        result["edits"] = {"type": "add", "generated_id": id}

        # If the type isn't 'add', we're probably replacing an error
        if edits and edits["type"] == "add":
            self.arc.delete(edits["generated_id"])

        return result

    def get(self, args, opts, edits):
        if not args:
            return {"error": "ID field is missing.", "usage": self.usage("get")}

        keys = ["id", "name", "tags", "link", "file", "notes"]
        values = self.arc.get(args[0], keys)

        if not values:
            return {"error": "Entry not found"}

        values = list(values)
        values[2], named_tags = extract_named_tags(values[2])

        result = {**dict(zip(keys, values)), **named_tags}
        result["edits"] = {"type": "get"}

        return result

    def find(self, args, opts, edits):
        fields = ["id", "name", "link", "tags"]
        del opts['author']

        opts = {k: group_args(v) for k, v in opts.items()}
        if args:
            opts["keyword"] = args[0]
        # opts = group_args(opts)
        result = self.arc.find(opts, fields)

        # Use a small slice as the answer
        items_per_page = 10
        page = opts.get("page", [1])[0] - 1
        keys, vals = unpack_tags_column(
            fields, 
            result[items_per_page * page : items_per_page * (page + 1)])

        cols = len(keys)
        dots = ["..."] * cols

        if page > 0:
            vals = [dots, *vals]

        if len(result) > items_per_page * (page + 1):
            vals.append(dots)

        return {"table": (vals, keys), "edits": {"type": "find"}}

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

        # Split free command arguments from the ones bound to a property (eg tags: somearg)
        free = [e for e in args if not isinstance(e, tuple)]
        other = dict(e for e in args if isinstance(e, tuple))
        opts = {**other, **extra}

        try:
            commands = {
                "add": self.add,
                "get": self.get,
                "find": self.find,
                "update": self.update,
                "help": self.help,
            }

            if name in commands:
                return commands[name](free, opts, edits)
            else:
                return {
                    "error": "%s is not a valid command." % name,
                    "usage": self.usage("general"),
                    "edits": edits
                }
        except Exception as e:
            return {"error": str(e), "edits": edits}

    # Parses the command message and calls the appropriate command handler
    def handle_message(self, message, extra):
        try:
            int_tree = grammar.parse(message)
            tree = grammar.transform(int_tree)

            # result = "```%s\n\n%s```" % (int_tree.pretty(), tree)
            return self.handle_command(tree[0], tree[1], extra)

        except grammar.exceptions.LarkError as error:
            print(error)
            return {
                "error": "```%s```" % error.args[0],
                "usage": self.usage("general"),
                "edits": extra.get("edits", None)
            }

