import grammar
import table


def group_opts(args):
    return dict(e for e in args if isinstance(e, tuple))


def free_opts(args):
    return [e for e in args if not isinstance(e, tuple)]


def handle_command(arc, name, args):
    free = free_opts(args)
    opts = group_opts(args)

    def add():
        link = free[0]
        return arc.add(link, opts.get("tags", []))

    def get():
        if len(free) == 1:
            return arc.get(free[0], ["id", "link", "tags"])

        return arc.get(free[0], free[1])

    def find():
        fields = free[0]
        result = arc.find(opts, fields)

        if result:
            return "```%s```" % table.tabulate(result, 150, fields)

        return "No entries found"

    def update():
        id = free[0]
        return arc.update(id, opts)

    try:
        return {"add": add, "get": get, "find": find, "update": update}[name]()
    except Exception as e:
        return e


def handle_message(arc, message):
    try:
        int_tree = grammar.parse(message)
        tree = grammar.transform(int_tree)

        # result = "```%s\n\n%s```" % (int_tree.pretty(), tree)
        result = handle_command(arc, tree[0], tree[1])

        if result:
            return str(result)

        return None

    except grammar.exceptions.LarkError as error:
        print(error)
        return None

