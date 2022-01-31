# parser.py
# parse a simple language with a simple recursive-descent parser

# Example code:
code = """
output 42
output 99
output 42 + 99 ; 141
output 42 - 3 - 8 + 4 ; 35
output 2*3+4 ; 10
output 2+3*4 ; 14

vars(x y)
set x to 5
output x

set y to 6
output y

{
    vars(y)
    set x to 7
    output x
    set y to 8
    output y
}

output x
output y

;set z to 22 ; undefined variable!
"""

from lexer import *

EOF_TOKEN = Token(EOF)

class Context(object):
    def __init__(self, parent=None):
        self.bindings = dict()
        self.parent = parent
    def getContext(self, varname):
        context = self
        while (context != None):
            if (varname in context.bindings):
                return context
            else:
                context = context.parent
        raise Exception("Undefined variable: " + varname)
    def get(self, varname):
        return self.getContext(varname).bindings[varname]
    def set(self, varname, value):
        self.getContext(varname).bindings[varname] = value

GLOBALS = Context()

class ParseNode(object):
    def __init__(self, *children):
        self.children = list(children)
    def printTree(self, depth=0):
        print "  "*depth, type(self).__name__
        for child in self.children:
            child.printTree(depth+1)
    def getChildren():
        return []

class Stmt(ParseNode):
    @classmethod
    def parse(cls, tokenBuffer):
        return (OutputStmt.parse(tokenBuffer) or
                SetStmt.parse(tokenBuffer) or
                BlockStmt.parse(tokenBuffer) or
                VarsStmt.parse(tokenBuffer))

class BlockStmt(Stmt):
    def eval(self, context=GLOBALS):
        result = None
        blockContext = Context(context)
        for stmt in self.children:
            result = stmt.eval(blockContext)
        return result
    @classmethod
    def parse(cls, tokenBuffer, topLevel=False):
        mark = tokenBuffer.getMark()
        if (topLevel or tokenBuffer.get().value == "{"):
            children = []
            while True:
                stmt = Stmt.parse(tokenBuffer)
                if (stmt == None):
                    break
                children.append(stmt)
            if (topLevel or tokenBuffer.get().value == "}"):
                return BlockStmt(*children)
        tokenBuffer.setMark(mark)
        return None

class SetStmt(Stmt):
    def eval(self, context):
        varname = self.children[0].id
        varval = self.children[1].eval(context)
        context.set(varname, varval)
        return varval
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        value = tokenBuffer.get().value
        if (value == "set"):
            id = Identifier.parse(tokenBuffer)
            if (id != None):
                value = tokenBuffer.get().value
                if (value == "to"):
                    expr = Expr.parse(tokenBuffer)
                    if (expr != None):
                        return SetStmt(id, expr)
        tokenBuffer.setMark(mark)
        return None

class VarsStmt(Stmt):
    def eval(self, context):
        idList = self.children[0]
        for varname in idList.ids:
            if (varname not in context.bindings):
                context.bindings[varname] = 0
        return 0
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        if (tokenBuffer.get().value == "vars"):
            idList = IdList.parse(tokenBuffer)
            if (idList != None):
                return VarsStmt(idList)
        tokenBuffer.setMark(mark)
        return None

class IdList(ParseNode):
    def __init__(self, ids):
        self.ids = ids
    def printTree(self, depth=0):
        print "  "*depth, type(self).__name__, "ids=", self.ids
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        if (tokenBuffer.get().value == "("):
            ids = [ ]
            while tokenBuffer.peek().value != ")":
                identifier = Identifier.parse(tokenBuffer)
                if (identifier == None):
                    raise Exception("Syntax error in IdList")
                ids.append(identifier.id)
            tokenBuffer.get() # eat the ")"
            return IdList(ids)
        tokenBuffer.setMark(mark)
        return SumExpr(*children)

class OutputStmt(Stmt):
    def eval(self, context):
        expr = self.children[0]
        result = expr.eval(context)
        print result
        return result
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        value = tokenBuffer.get().value
        if (value == "output"):
            expr = Expr.parse(tokenBuffer)
            if (expr != None):
                return OutputStmt(expr)
        tokenBuffer.setMark(mark)
        return None

class Expr(Stmt):
    @classmethod
    def parse(cls, tokenBuffer):
        return SumExpr.parse(tokenBuffer)

class SumExpr(Expr):
    def eval(self, context):
        result = self.children[0].eval(context)
        for i in range(1, len(self.children), 2):
            op = self.children[i].op
            arg = self.children[i+1].eval(context)
            if (op == "+"):
                result += arg
            elif (op == "-"):
                result -= arg
            else:
                raise Exception("Unknown op:" + str(op))
        return result
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        expr = ProductExpr.parse(tokenBuffer)
        if (expr == None):
            tokenBuffer.setMark(mark)
            return None
        children = [expr]
        while True:
            mark = tokenBuffer.getMark()
            op = SumOperator.parse(tokenBuffer)
            if (op == None):
                break
            expr = ProductExpr.parse(tokenBuffer)
            if (expr == None):
                break
            children += [op, expr]
        tokenBuffer.setMark(mark)
        return SumExpr(*children)

class ProductExpr(Expr):
    def eval(self, context):
        result = self.children[0].eval(context)
        for i in range(1, len(self.children), 2):
            op = self.children[i].op
            arg = self.children[i+1].eval(context)
            if (op == "*"):
                result *= arg
            elif (op == "/"):
                result /= arg
            elif (op == "%"):
                result %= arg
            else:
                raise Exception("Unknown op:" + str(op))
        return result
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        expr = SimpleExpr.parse(tokenBuffer)
        if (expr == None):
            tokenBuffer.setMark(mark)
            return None
        children = [expr]
        while True:
            mark = tokenBuffer.getMark()
            op = ProductOperator.parse(tokenBuffer)
            if (op == None):
                break
            expr = SimpleExpr.parse(tokenBuffer)
            if (expr == None):
                break
            children += [op, expr]
        tokenBuffer.setMark(mark)
        return ProductExpr(*children)

class Operator(ParseNode):
    def __init__(self, op):
        self.op = op
    def printTree(self, depth=0):
        print "  "*depth, type(self).__name__, "op=", self.op
    def eval(self, context):
        return self.value
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        value = tokenBuffer.get().value
        if (value in cls.getOps()):
            return Operator(value)
        tokenBuffer.setMark(mark)
        return None

class SumOperator(Operator):
    @classmethod
    def getOps(cls): return "+-"

class ProductOperator(Operator):
    @classmethod
    def getOps(cls): return "*/%"

class SimpleExpr(Expr):
    # a literal or a variable
    @classmethod
    def parse(cls, tokenBuffer):
        return (Literal.parse(tokenBuffer) or
                Identifier.parse(tokenBuffer))

class Identifier(SimpleExpr):
    def __init__(self, id):
        self.id = id
    def printTree(self, depth=0):
        print "  "*depth, type(self).__name__, "id=", self.id
    def eval(self, context):
        return context.get(self.id)
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        value = tokenBuffer.get().value
        if (type(value) == str):
            return Identifier(value)
        tokenBuffer.setMark(mark)
        return None

class Literal(SimpleExpr):
    def __init__(self, value):
        self.value = value
    def printTree(self, depth=0):
        print "  "*depth, type(self).__name__, "value=", self.value
    def eval(self, context):
        return self.value
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        value = tokenBuffer.get().value
        if (type(value) == int):
            return Literal(value)
        tokenBuffer.setMark(mark)
        return None

def parseTopLevelBlock(code):
    tokenBuffer = Buffer(tokenize(code), EOF_TOKEN)
    result = BlockStmt.parse(tokenBuffer, True)
    if (tokenBuffer.peek() != EOF_TOKEN):
        raise Exception("extra input: " + str(tokenBuffer.get()))
    return result

def parseStmtOrExpr(code, tryExpr=False):
    tokenBuffer = Buffer(tokenize(code), EOF_TOKEN)
    result = Stmt.parse(tokenBuffer)
    if (tokenBuffer.peek() != EOF_TOKEN) and tryExpr:
        tokenBuffer.rewind()
        result = Expr.parse(tokenBuffer)
    if (tokenBuffer.peek() != EOF_TOKEN):
        raise Exception("extra input: " + str(tokenBuffer.get()))
    return result

import sys, traceback
def repl():
    print "**************************************************"
    print "Read-Eval-Print loop ('quit' or 'exit' when done)."
    while True:
        code = raw_input("--> ")
        if (code in ["quit", "exit"]):
            break
        try:
            ast = parseStmtOrExpr(code, True)
            output = ast.eval(GLOBALS)
            print output
        except Exception as error:
            print "Error:", error
            traceback.print_exc(file=sys.stdout)

if (__name__ == "__main__"):
    ast = parseTopLevelBlock(code)
    ast.printTree()
    ast.eval()
    repl()
