import texttable
import math


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
