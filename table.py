import texttable
import math


def prepare_value(value, max_col_width=None):
    if isinstance(value, str):
        if max_col_width and len(value > max_col_width):
            return value[: max_col_width - 3] + "..."

        return value

    if hasattr(value, "__iter__"):
        return prepare_value(", ".join(sorted(value)), max_col_width)

    if value == None:
        return ""

    return prepare_value(str(value), max_col_width)


def prepare(rows, max_col_width=None):
    result = []

    for row in rows:
        result.append(tuple(prepare_value(v, max_col_width) for v in row))

    return result


def tabulate(rows, max_width, headers=False):
    table = texttable.Texttable(max_width)
    table.add_rows(rows, header=False)

    if headers:
        table.header(headers)

    table.set_chars(["", "", "", "-"])

    return table.draw()


# Draws a table from a dictionary with a format like:
# table = {
#   "headerA": [a1, a2, a3],
#   "headerB": [b1, b2, b3]
# }
def tabulate_dict(table, max_width):
    headers = table.keys()
    rows = zip(*table.values())

    return tabulate(rows, max_width, headers)
