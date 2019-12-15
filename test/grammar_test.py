import unittest
import grammar


class TestGrammar(unittest.TestCase):
    def test_grammar(self):
        g = grammar.build_grammar()

        for s in [
            '!add link tags: [one, two] description: "looks really cool"',
            "!edit 123 tags: [three]",
            "!get 123",
            '!find "keyword"',
            '!find tags: [one, two, "three"]',
            "!update 123 tags: +[four, five, seven] -one",
        ]:
            print("\nPARSING '%s':\n" % s, g.parse(s).pretty())
