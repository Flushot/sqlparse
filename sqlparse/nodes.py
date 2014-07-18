from abc import ABCMeta, abstractmethod
from decimal import Decimal


class ASTNode(object):
    """
    Node in abstract syntax tree
    """
    __metaclass__ = ABCMeta


class Value(ASTNode):
    __metaclass__ = ABCMeta


class StringValue(Value):
    """
    'value'
    "value"
    """
    def __init__(self, tokens):
        self.value = tokens[0][1:-1]


class IntegerValue(Value):
    """
    ... -1 0 1 2 ...
    """
    def __init__(self, tokens):
        self.value = int(tokens[0])


class RealValue(Value):
    """
    .1
    1.2
    -1.23
    1.2e3
    1.2e-3
    """
    def __init__(self, tokens):
        self.value = Decimal(tokens[0])


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



class Identifier(ASTNode):
    """

    """
    def __init__(self, tokens):
        self.name = tokens[0][0]


class ModelIdentifier(Identifier):
    pass


class ProjectionExpression(ASTNode):
    def __init__(self, tokens):
        self.projection = tokens[0]


class PredicateExpression(ASTNode):
    """
    Expression that can be used for filtering, such as in a SELECT, WHERE,
    ON clause, or HAVING function
    """
    def __init__(self, tokens):
        self.expression = tokens[0]


class Function(ASTNode):
    """
    Commonly used for aggregate functions (e.g. MIN,MAX,AVG,etc.)

    f(x,y)
    """
    __metaclass__ = ABCMeta

    def __init__(self, tokens):
        self.name, self.args = tokens[0]
        self.name = self.name.lower()



class UnaryOperator(Function):
    """
    -x +x ~x
    not
    """
    def __init__(self, tokens):
        super(UnaryOperator, self).__init__(tokens)
        self.rhs = self.args

    def __repr__(self):
        return '(%s %s)' % (self.name, self.args)


class BinaryOperator(Function):
    """
    x+y x-y x*y x**y x^y x/y
    | & << <<< >> >>> or xor and in
    """
    def __init__(self, tokens):
        self.lhs, self.name, self.rhs = tokens[0]
        self.args = (self.lhs, self.rhs)
        #super(BinaryOperator, self).__init__()

    def __repr__(self):
        return '(%s %s %s)' % (self.name, self.lhs, self.rhs)


class Statement(ASTNode):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
