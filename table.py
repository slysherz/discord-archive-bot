import texttable
import math


def tabulate(rows, max_width, headers=False):
    table = texttable.Texttable(max_width)
    table.add_rows(rows, header=False)

    if headers:
        table.header(headers)

    table.set_chars(["", "", "", "-"])

    return table.draw()

