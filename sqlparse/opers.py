from abc import ABCMeta


class Operator(object):
    __meta__ = ABCMeta


class Value(object):
    __meta__ = ABCMeta


class Identifier(object):
    __meta__ = ABCMeta


class UnaryOperator(Operator):
    """
    -x +x ~x
    not
    """
    def __init__(self, tokens):
        self.op, self.rhs = tokens[0]

    def __repr__(self):
        return '(%s %s)' % (self.op, self.rhs)


class BinaryOperator(Operator):
    """
    x+y x-y x*y x**y x^y x/y x//y
    | & << <<< >> >>> or xor and in
    """
    def __init__(self, tokens):
        self.lhs, self.op, self.rhs = tokens[0]

    def __repr__(self):
        return '(%s %s %s)' % (self.op, self.lhs, self.rhs)


class ListValue(Value):
    """
    [x,y,...]
    (x,y,...)
    """
    def __init__(self, tokens):
        self.values = list(tokens[0])
        self.frozen = False

    def __repr__(self):
        return "'(%s)" % ' '.join(map(str, self.values))


class RangeValue(Value):
    """
    [x...y]
    (x...y)
    between x and y
    """
    def __init__(self, tokens):
        self.begin, self.end = tokens[0]

    def __repr__(self):
        return "%s...%s" % (self.begin, self.end)
