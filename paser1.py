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

;set x to 5
;set y to 3
;set z to sum(x,y)
;output z

"""

from lexer import *

EOF_TOKEN = Token(EOF)

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
        return (OutputStmt.parse(tokenBuffer))

class BlockStmt(Stmt):
    def eval(self):
        result = None
        for stmt in self.children:
            result = stmt.eval()
        return result
    @classmethod
    def parse(cls, tokenBuffer):
        block = BlockStmt()
        while True:
            stmt = Stmt.parse(tokenBuffer)
            if (stmt == None):
                break
            block.children.append(stmt)
        return block

class OutputStmt(Stmt):
    def eval(self):
        expr = self.children[0]
        result = expr.eval()
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
    pass
    @classmethod
    def parse(cls, tokenBuffer):
        return SumExpr.parse(tokenBuffer)

class SumExpr(Expr):
    def eval(self):
        result = self.children[0].eval()
        for i in range(1, len(self.children), 2):
            op = self.children[i].op
            arg = self.children[i+1].eval()
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
    def eval(self):
        result = self.children[0].eval()
        for i in range(1, len(self.children), 2):
            op = self.children[i].op
            arg = self.children[i+1].eval()
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
        expr = LiteralExpr.parse(tokenBuffer)
        if (expr == None):
            tokenBuffer.setMark(mark)
            return None
        children = [expr]
        while True:
            mark = tokenBuffer.getMark()
            op = ProductOperator.parse(tokenBuffer)
            if (op == None):
                break
            expr = LiteralExpr.parse(tokenBuffer)
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
    def eval(self):
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

class LiteralExpr(Expr):
    def __init__(self, value):
        self.value = value
    def printTree(self, depth=0):
        print "  "*depth, type(self).__name__, "value=", self.value
    def eval(self):
        return self.value
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        value = tokenBuffer.get().value
        if (type(value) == int):
            return LiteralExpr(value)
        tokenBuffer.setMark(mark)
        return None

def parseTopLevelBlockStmt(code):
    tokenBuffer = Buffer(tokenize(code), EOF_TOKEN)
    result = BlockStmt.parse(tokenBuffer)
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
            output = ast.eval()
            print output
        except Exception as error:
            print "Error:", error
            traceback.print_exc(file=sys.stdout)

if (__name__ == "__main__"):
    ast = parseTopLevelBlockStmt(code)
    ast.printTree()
    ast.eval()
    repl()
