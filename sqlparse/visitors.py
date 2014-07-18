from nodevisitor import ASTVisitor


class IdentifierVisitor(ASTVisitor):
    def visit_Identifier(self, node):
        # TODO: parse . notation
        return unicode(node.name)


class ValueVisitor(ASTVisitor):
    def visit_StringValue(self, node):
        return unicode(node.value)

    def visit_IntegerValue(self, node):
        return int(node.value)

    def visit_RealValue(self, node):
        return str(node.value)  # str = no precision loss

    def visit_ListValue(self, node):
        return list(node.values)

    def visit_RangeValue(self, node):
        raise NotImplementedError()


class IdentifierAndValueVisitor(IdentifierVisitor, ValueVisitor):
    pass
