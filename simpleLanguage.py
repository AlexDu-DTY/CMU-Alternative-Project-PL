# simpleLanguage.py
# a trivially simple language with trivially simple lexing
# and recursive-descent parsing.  This is (obviously) only
# for demonstrational purposes, and most assuredly is riddled
# with bugs and pedagogically-motivated (read: not practical)
# design decisions.  Do not use this code!

# Example code:
code = """
vars(rfib ifib counter)

; rfib: recursive fibonacci
set rfib to function(n) {
    if n is 0 then { return 1 }
    if n is 1 then { return 1 }
    return rfib(n-1) + rfib(n-2)
}

loop counter from 0 to 6 { output rfib(counter) }

; ifib: iterative fibonacci
set ifib to function(n) {
    vars(x y temp counter)
    if n is 0 then { return 1 }
    if n is 1 then { return 1 }
    set x to 1
    set y to 1
    loop counter from 2 to n
    {
        set temp to x + y
        set x to y
        set y to temp
    }
    return y
}

loop counter from 0 to 6 { output ifib(counter) }

"""

##############################################
## Lexer
##############################################

# tokenize a string according to a regular grammar
# also, elide comments and whitespace
# more classically done with RegEx -> NDFA -> DFA

COMMENT_START = ";"
COMMENT_END = "\n"
EOF = chr(0)

class Token(object):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return "Token(%r)" % (self.value)
    def eof(self):
        return self.value == EOF

class Buffer(object):
    def __init__(self, sequence, terminator=EOF):
        self.sequence = sequence
        self.next = 0
        self.terminator = terminator
    def hasNext(self):
        return self.next < len(self.sequence)
    def peek(self):
        if (self.hasNext()):
            return self.sequence[self.next]
        else:
            return self.terminator
    def get(self):
        ch = self.peek()
        if (ch != self.terminator): self.next += 1
        return ch
    def unget(self):
        if (self.next > 0): self.next -= 1
    def getMark(self):
        return self.next
    def setMark(self, mark):
        self.next = mark
    def rewind(self):
        self.next = 0

def tokenize(code):
    tokens = []
    buffer = Buffer(code)
    while buffer.hasNext():
        ch = buffer.peek()
        if (ch == COMMENT_START):
            eatComment(buffer)
        elif (ch.isdigit()):
            tokens.append(tokenizeInt(buffer))
        elif (ch.isalpha()):
            tokens.append(tokenizeId(buffer))
        elif (ch.isspace()):
            buffer.get() # eat the whitespace and continue
        elif (ch in "=+-*/(){}"):
            tokens.append(Token(buffer.get()))
        else:
            raise Exception("Illegal character: " + str(ch))
    return tokens

def eatComment(buffer):
    while True:
        if (buffer.get() in [COMMENT_END, EOF]):
            return

def tokenizeInt(buffer):
    result = 0
    while (buffer.peek().isdigit()):
        result = 10*result + int(buffer.get())
    return Token(result)

def tokenizeId(buffer):
    result = ""
    while (buffer.peek().isalnum()):
        result += buffer.get()
    return Token(result)

def testLexer():
    code = """
    x = 123 ; set x
            ; to 123!
    y = 456 + 78
    
    """
    print(tokenize(code))

##############################################
## Parser and Evaluator
##############################################

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

class ReturnStmtException(Exception):
    def __init__(self, result):
        self.result = result

class ParseNode(object):
    def __init__(self, *children):
        self.children = list(children)
    def printTree(self, depth=0):
        print ("  "*depth, type(self).__name__)
        for child in self.children:
            if (isinstance(child, ParseNode)):
                child.printTree(depth+1)
            else:
                raise Exception("Non-PrintNode: ", child)
    def getChildren():
        return []

class Stmt(ParseNode):
    @classmethod
    def parse(cls, tokenBuffer):
        return (OutputStmt.parse(tokenBuffer) or
                SetStmt.parse(tokenBuffer) or
                ReturnStmt.parse(tokenBuffer) or
                BlockStmt.parse(tokenBuffer) or
                VarsStmt.parse(tokenBuffer) or
                IfStmt.parse(tokenBuffer) or
                LoopStmt.parse(tokenBuffer))

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

class ReturnStmt(Stmt):
    def eval(self, context):
        result = self.children[0].eval(context)
        raise ReturnStmtException(result)
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        if (tokenBuffer.get().value == "return"):
            expr = Expr.parse(tokenBuffer)
            if (expr != None):
                return ReturnStmt(expr)
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

class IfStmt(Stmt):
    def eval(self, context):
        varname = self.children[0].id
        varval = context.get(varname)
        targetval = self.children[1].eval(context)
        if (varval == targetval):
            return self.children[2].eval(context)
        elif (len(self.children) == 3):
            # no else clause
            return 0
        else:
            return self.children[3].eval(context)
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        if (tokenBuffer.get().value == "if"):
            identifier = Identifier.parse(tokenBuffer)
            if (identifier == None):
                raise Exception("Missing identifier in 'if'")
            if (tokenBuffer.get().value != "is"):
                raise Exception("Missing 'is' in 'if'")
            expr = Expr.parse(tokenBuffer)
            if (expr == None):
                raise Exception("Missing expr in 'if'")
            if (tokenBuffer.get().value != "then"):
                raise Exception("Missing 'then' in 'if'")
            thenBlock = BlockStmt.parse(tokenBuffer)
            if (thenBlock == None):
                raise Exception("Missing thenBlock in 'if'")
            if (tokenBuffer.peek().value == "else"):
                tokenBuffer.get() # eat the "else"
                elseBlock = BlockStmt.parse(tokenBuffer)
                if (elseBlock == None):
                    raise Exception("Missing block in 'else'")
                return IfStmt(identifier, expr, thenBlock, elseBlock)
            else:
                # no else block, so omit it from children
                return IfStmt(identifier, expr, thenBlock)
        tokenBuffer.setMark(mark)
        return None

class LoopStmt(Stmt):
    def eval(self, context):
        varName = self.children[0].id
        fromVal = self.children[1].eval(context)
        toVal = self.children[2].eval(context)
        step = +1 if (fromVal<toVal) else -1
        block = self.children[3]
        result = None
        for varVal in range(fromVal, toVal+step, step): #
            context.set(varName, varVal)
            result = block.eval(context)
        return result
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        if (tokenBuffer.get().value == "loop"):
            identifier = Identifier.parse(tokenBuffer)
            if (identifier == None):
                raise Exception("Missing identifier in 'loop'")
            if (tokenBuffer.get().value != "from"):
                raise Exception("Missing 'from' in 'loop'")
            fromExpr = Expr.parse(tokenBuffer)
            if (fromExpr == None):
                raise Exception("Missing fromExpr in 'loop'")
            if (tokenBuffer.get().value != "to"):
                raise Exception("Missing 'to' in 'loop'")
            toExpr = Expr.parse(tokenBuffer)
            if (toExpr == None):
                raise Exception("Missing toExpr in 'loop'")
            block = BlockStmt.parse(tokenBuffer)
            if (block == None):
                raise Exception("Missing block in 'loop'")
            return LoopStmt(identifier, fromExpr, toExpr, block)
        tokenBuffer.setMark(mark)
        return None

class ExprList(ParseNode):
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        if (tokenBuffer.get().value == "("):
            exprs = [ ]
            while tokenBuffer.peek().value != ")":
                expr = Expr.parse(tokenBuffer)
                if (expr == None):
                    raise Exception("Syntax error in ExprList")
                exprs.append(expr)
            tokenBuffer.get() # eat the ")"
            return ExprList(*exprs)
        tokenBuffer.setMark(mark)
        return None

class IdList(ParseNode):
    def __init__(self, ids):
        self.ids = ids
    def printTree(self, depth=0):
        print("  "*depth, type(self).__name__, "ids=", self.ids)
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
        return None

class OutputStmt(Stmt):
    def eval(self, context):
        expr = self.children[0]
        result = expr.eval(context)
        print(result)
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
        return (FunctionExpr.parse(tokenBuffer) or
                SumExpr.parse(tokenBuffer))

class FunctionExpr(Expr):
    def eval(self, context):
        return self
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        if (tokenBuffer.get().value == "function"):
            idList = IdList.parse(tokenBuffer)
            if (idList == None):
                raise Exception("Missing idList in function")
            block = BlockStmt.parse(tokenBuffer)
            if (block == None):
                raise Exception("Missing block in function")            
            return FunctionExpr(idList, block)
        tokenBuffer.setMark(mark)
        return None

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
        print ("  "*depth, type(self).__name__, "op=", self.op)
    def eval(self, context):
        return self.value
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        value = tokenBuffer.get().value
        if (type(value) == str) and (value in cls.getOps()):
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
                FunctionCall.parse(tokenBuffer) or
                Identifier.parse(tokenBuffer))

class FunctionCall(SimpleExpr):
    def eval(self, context):
        fnName = self.children[0].id
        exprList = self.children[1].children
        exprs = [ ]
        for expr in exprList:
            exprs.append(expr.eval(context))
        fn = context.get(fnName)
        if (not isinstance(fn, FunctionExpr)):
            raise Exception("Not a function: " + fnName)
        idList = fn.children[0].ids
        block = fn.children[1]
        if (len(idList) != len(exprList)):
            raise Exception("Wrong # of arguments: " + fnName)
        fnContext = Context(context)
        for i in range(len(idList)):
            varname = idList[i]
            varvalue = exprList[i].eval(context)
            fnContext.bindings[varname] = varvalue
        try:
            return block.eval(fnContext)
        except ReturnStmtException as returnStmt:
            return returnStmt.result
    @classmethod
    def parse(cls, tokenBuffer):
        mark = tokenBuffer.getMark()
        identifier = Identifier.parse(tokenBuffer)
        if (identifier != None):
            exprList = ExprList.parse(tokenBuffer)
            if (exprList != None):
                return FunctionCall(identifier, exprList)
        tokenBuffer.setMark(mark)
        return None

class Identifier(SimpleExpr):
    def __init__(self, id):
        self.id = id
    def printTree(self, depth=0):
        print ("  "*depth, type(self).__name__, "id=", self.id)
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
        print ("  "*depth, type(self).__name__, "value=", self.value)
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

##############################################
## Top-Level Parsing and REPL (Read-Eval-Print Loop)
##############################################

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
    print ("**************************************************")
    print ("Read-Eval-Print loop ('quit' or 'exit' when done).")
    while True:
        code = raw_input("--> ")
        if (code in ["quit", "exit"]):
            break
        try:
            ast = parseStmtOrExpr(code, True)
            output = ast.eval(GLOBALS)
            print (output)
        except Exception as error:
            print ("Error:", error)
            traceback.print_exc(file=sys.stdout)

if (__name__ == "__main__"):
    ast = parseTopLevelBlock(code)
    ast.printTree()
    ast.eval()
    repl()
