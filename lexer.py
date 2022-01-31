# lexer.py
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
    print tokenize(code)

if (__name__ == "__main__"):
    testLexer()
