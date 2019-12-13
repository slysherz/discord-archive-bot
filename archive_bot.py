import grammar


def group_opts(args):
    return dict(e for e in args if isinstance(e, tuple))


def free_opts(args):
    return [e for e in args if not isinstance(e, tuple)]


class ArchiveBot:
    def __init__(self, archive):
        self.arc = archive

    def get_resume(self, id):
        keys = ["id", "name", "tags"]

        return dict(zip(keys, self.arc.get(id, keys)))

    def get_usage(self):
        return {
            "usage": "get",
            "syntax": "!get [id]",
            "examples": ["!get 123"],
        }

    def update_usage(self):
        return {
            "usage": "update",
            "syntax": "!update [id] ...options",
            "examples": ["!update 123 name: newname tags: [newone, newtwo]"],
        }

    def add(self, args, opts):
        if len(args):
            opts["link"] = args[0]

        if not ("link" in opts or "file" in opts):
            return {"error": "Entry must contain either a link or a file"}

        id = self.arc.add(opts)
        return self.get_resume(id)

    def get(self, args, opts):
        if not args:
            return {"error": "ID field is missing.", "usage": self.get_usage()}

        keys = ["id", "name", "tags", "link", "file"]
        values = self.arc.get(args[0], keys)

        if not values:
            return {"error": "Entry not found"}

        result = dict(zip(keys, values))

        return result

    def find(self, args, opts):
        fields = ["id", "name", "link", "tags"]
        if args:
            fields = args[0]

        result = self.arc.find(opts, fields)

        return {"table": (result, fields)}

    def update(self, args, opts):
        if not args:
            return {"error": "ID field is missing.", "usage": self.update_usage()}

        id = self.arc.update(args[0], opts)

        return self.get_resume(id)

    def handle_command(self, name, args, extra):
        free = free_opts(args)
        opts = {**group_opts(args), **extra}

        try:
            return {
                "add": self.add,
                "get": self.get,
                "find": self.find,
                "update": self.update,
            }[name](free, opts)
        except Exception as e:
            return {"error": e}

    def handle_message(self, message, extra):
        try:
            int_tree = grammar.parse(message)
            tree = grammar.transform(int_tree)

            # result = "```%s\n\n%s```" % (int_tree.pretty(), tree)
            return self.handle_command(tree[0], tree[1], extra)

        except grammar.exceptions.LarkError as error:
            print(error)
            return None

