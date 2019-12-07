from lark import Lark
from lark import exceptions
from lark import Transformer


def build_grammar():
    with open("command_grammar.lark", "r") as file:
        return Lark(file.read(), start="command")


# Transforms the tree generated by lark into what we actually want
class CommandTransformer(Transformer):
    def STRING(self, s):
        return s[1:-1]

    def command(self, args):
        return args

    named_parameter = tuple
    list = list
    command_body = list
    WORD = str
    NUMBER = int


command_grammar = build_grammar()
command_transformer = CommandTransformer(visit_tokens=True)

parse = command_grammar.parse
transform = command_transformer.transform
