import unittest
import grammar
from grammar import Add, Sub

g = grammar.build_grammar()


def parse(command):
    print("\nPARSING '%s':\n" % command)
    parsed = g.parse(command)

    print(parsed.pretty())

    transformed = grammar.transform(parsed)
    print(transformed)

    return transformed


class TestGrammar(unittest.TestCase):
    def test_grammar(self):

        for s in [
            "!add link tags: author:slysherz score:1",
            '!add link tags: [one, two] description: "looks really cool"',
            "!edit 123 tags: [three]",
            "!get 123",
            '!find "keyword"',
            '!find tags: [one, two, "three"]',
            "!update 123 tags: +[four, five, seven] -one",
        ]:
            parsed = g.parse(s)
            print("\nPARSING '%s':\n" % s, parsed.pretty())

            transformed = grammar.transform(parsed)
            print(transformed)

    def test_grammar2(self):
        self.assertEqual(
            parse("!add link tags: author:slysherz score:1"),
            ["add", ["link", ("tags", ["author:slysherz", "score:1"])]],
        )

        self.assertEqual(
            parse('!add link tags: [one, two] description: "looks really cool"'),
            [
                "add",
                [
                    "link",
                    ("tags", [["one", "two"]]),
                    ("description", ["looks really cool"]),
                ],
            ],
        )

        self.assertEqual(
            parse("!update 123 tags: +[four, five, seven] -one"),
            ["update", [123, ("tags", [Add(["four", "five", "seven"]), Sub("one")])],],
        )

        self.assertEqual(
            parse("!find keyword [id, tags] tags: +author:? -score:?"),
            [
                "find",
                [
                    "keyword",
                    ["id", "tags"],
                    ("tags", [Add("author:?"), Sub("score:?")]),
                ],
            ],
        )

