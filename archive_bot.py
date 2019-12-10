import grammar
import table


def group_opts(args):
    return dict(e for e in args if isinstance(e, tuple))


def free_opts(args):
    return [e for e in args if not isinstance(e, tuple)]


class ArchiveBot:
    def __init__(self, archive):
        self.arc = archive

    def handle_command(self, name, args, extra):
        free = free_opts(args)
        opts = {**group_opts(args), **extra}

        def add():
            link = free[0]
            return self.arc.add(link, opts)

        def get():
            result = self.arc.get(free[0], ["id", "link", "tags", "file"])

            if not result:
                return "Entry with id %s not found" % id

            file = result[3]

            if file:
                return result[0:3], {"file": file}

            return result

        def find():
            fields = free[0]
            result = self.arc.find(opts, fields)

            if result:
                return "```%s```" % table.tabulate(result, 150, fields)

            return "No entries found"

        def update():
            id = free[0]
            return self.arc.update(id, opts)

        try:
            return {"add": add, "get": get, "find": find, "update": update}[name]()
        except Exception as e:
            return e

    def handle_message(self, message, extra):
        try:
            int_tree = grammar.parse(message)
            tree = grammar.transform(int_tree)

            # result = "```%s\n\n%s```" % (int_tree.pretty(), tree)
            result = self.handle_command(tree[0], tree[1], extra)

            if isinstance(result, tuple):
                return result

            if result:
                return str(result)

            return None

        except grammar.exceptions.LarkError as error:
            print(error)
            return None
