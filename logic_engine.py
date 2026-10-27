"""Boolean expression engine for LogicLab.

Tokenizer -> recursive-descent parser -> AST -> evaluator / truth table.
Nothing here uses eval() or exec(), and nothing depends on Flask.

Precedence (highest to lowest): NOT, AND, XOR, OR. Parentheses override it.
"""
from dataclasses import dataclass
from itertools import product

MAX_EXPRESSION_LENGTH = 200
MAX_VARIABLES = 4
MAX_DEPTH = 40  # nested parentheses / chained NOTs; keeps recursion shallow


class LogicError(ValueError):
    """A user-facing problem with an expression. `position` is a 0-based index or None."""

    def __init__(self, message, position=None):
        super().__init__(message)
        self.message = message
        self.position = position


# ---------------------------------------------------------------- tokenizer
KEYWORDS = {"AND", "OR", "NOT", "XOR"}
SYMBOLS = {
    "∧": "AND", "&": "AND",
    "∨": "OR", "|": "OR",
    "⊕": "XOR", "^": "XOR",
    "¬": "NOT", "!": "NOT", "~": "NOT",
}
OPERAND_STARTS = ("VAR", "CONST", "NOT", "LPAREN")


@dataclass(frozen=True)
class Token:
    kind: str   # VAR CONST AND OR XOR NOT LPAREN RPAREN END
    value: str
    pos: int


def tokenize(text):
    if not isinstance(text, str):
        raise LogicError("Expression must be text.")
    if not text.strip():
        raise LogicError("Please enter an expression, for example: A AND B")
    if len(text) > MAX_EXPRESSION_LENGTH:
        raise LogicError(f"Expression is too long (maximum {MAX_EXPRESSION_LENGTH} characters).")

    tokens, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == "(":
            tokens.append(Token("LPAREN", ch, i)); i += 1
        elif ch == ")":
            tokens.append(Token("RPAREN", ch, i)); i += 1
        elif ch in SYMBOLS:
            tokens.append(Token(SYMBOLS[ch], ch, i)); i += 1
        elif ch in "01":
            tokens.append(Token("CONST", ch, i)); i += 1
        elif ch.isascii() and ch.isalpha():
            j = i
            while j < len(text) and text[j].isascii() and text[j].isalpha():
                j += 1
            word = text[i:j]
            if word.upper() in KEYWORDS:
                tokens.append(Token(word.upper(), word, i))
            elif len(word) == 1:
                tokens.append(Token("VAR", word.upper(), i))
            else:
                raise LogicError(
                    f"Unknown word '{word}'. Variables are single letters (A-Z); "
                    "operators are AND, OR, NOT, XOR.", i)
            i = j
        else:
            raise LogicError(f"Unsupported character '{ch}' at position {i + 1}.", i)
    tokens.append(Token("END", "", len(text)))
    return tokens


# ---------------------------------------------------------------------- AST
@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Const:
    value: int


@dataclass(frozen=True)
class Not:
    operand: object


@dataclass(frozen=True)
class BinOp:
    op: str  # "AND" | "OR" | "XOR"
    left: object
    right: object


# ------------------------------------------------------------------- parser
class _Parser:
    LEVELS = ("OR", "XOR", "AND")  # lowest precedence first

    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
        self.depth = 0

    def peek(self):
        return self.tokens[self.i]

    def advance(self):
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def parse(self):
        node = self.binary(0)
        tok = self.peek()
        if tok.kind != "END":
            raise self.after_operand_error(tok)
        return node

    @staticmethod
    def after_operand_error(tok):
        if tok.kind == "RPAREN":
            return LogicError(f"Unmatched closing parenthesis at position {tok.pos + 1}.", tok.pos)
        return LogicError(
            f"Missing operator before '{tok.value}' at position {tok.pos + 1}. "
            "Use AND, OR or XOR between operands.", tok.pos)

    def binary(self, level):
        if level == len(self.LEVELS):
            return self.unary()
        op = self.LEVELS[level]
        left = self.binary(level + 1)
        while self.peek().kind == op:
            self.advance()
            left = BinOp(op, left, self.binary(level + 1))
        return left

    def enter(self, tok):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise LogicError(f"Expression is nested too deeply (maximum {MAX_DEPTH} levels).", tok.pos)

    def unary(self):
        tok = self.peek()
        if tok.kind == "NOT":
            self.advance()
            self.enter(tok)
            node = Not(self.unary())
            self.depth -= 1
            return node
        return self.primary()

    def primary(self):
        tok = self.peek()
        if tok.kind == "VAR":
            self.advance()
            return Var(tok.value)
        if tok.kind == "CONST":
            self.advance()
            return Const(int(tok.value))
        if tok.kind == "LPAREN":
            self.advance()
            self.enter(tok)
            node = self.binary(0)
            nxt = self.peek()
            if nxt.kind != "RPAREN":
                if nxt.kind in OPERAND_STARTS:
                    raise self.after_operand_error(nxt)
                raise LogicError(f"Missing closing parenthesis for '(' at position {tok.pos + 1}.", tok.pos)
            self.advance()
            self.depth -= 1
            return node
        if tok.kind == "END":
            prev = self.tokens[self.i - 1].value
            raise LogicError(f"The expression ended unexpectedly: an operand is missing after '{prev}'.", tok.pos)
        raise LogicError(f"Missing operand before '{tok.value}' at position {tok.pos + 1}.", tok.pos)


def parse_expression(text):
    """Parse text into an AST. Raises LogicError for anything invalid."""
    ast = _Parser(tokenize(text)).parse()
    names = variables(ast)
    if len(names) > MAX_VARIABLES:
        raise LogicError(
            f"Too many variables ({len(names)}: {', '.join(names)}). "
            f"LogicLab supports at most {MAX_VARIABLES}.")
    return ast


# --------------------------------------------------------------- evaluation
def variables(ast):
    """Sorted, de-duplicated variable names (deterministic order)."""
    found = set()

    def walk(n):
        if isinstance(n, Var):
            found.add(n.name)
        elif isinstance(n, Not):
            walk(n.operand)
        elif isinstance(n, BinOp):
            walk(n.left); walk(n.right)

    walk(ast)
    return sorted(found)


def evaluate(ast, env):
    """Evaluate with env = {"A": 0/1, ...}. Returns 0 or 1."""
    if isinstance(ast, Var):
        if ast.name not in env:
            raise LogicError(f"No value was provided for variable {ast.name}.")
        return 1 if env[ast.name] else 0
    if isinstance(ast, Const):
        return ast.value
    if isinstance(ast, Not):
        return 1 - evaluate(ast.operand, env)
    left, right = evaluate(ast.left, env), evaluate(ast.right, env)
    if ast.op == "AND":
        return left & right
    if ast.op == "OR":
        return left | right
    if ast.op == "XOR":
        return left ^ right
    raise LogicError(f"Unsupported operator {ast.op}.")


def truth_table(ast):
    """All 2^n rows in binary counting order (first variable = most significant bit)."""
    names = variables(ast)
    rows = []
    for combo in product((0, 1), repeat=len(names)):
        rows.append({"inputs": list(combo), "output": evaluate(ast, dict(zip(names, combo)))})
    return rows


def row_index(bits):
    """Index of an input combination within the truth table."""
    index = 0
    for b in bits:
        index = index * 2 + (1 if b else 0)
    return index


# ------------------------------------------------------------- explanation
def _operand(n):
    return str(n.name) if isinstance(n, Var) else str(n.value) if isinstance(n, Const) else f"({to_string(n)})"


def to_string(ast):
    """Canonical text; every nested compound operand is parenthesised."""
    if isinstance(ast, Var):
        return ast.name
    if isinstance(ast, Const):
        return str(ast.value)
    if isinstance(ast, Not):
        return f"NOT {_operand(ast.operand)}"
    return f"{_operand(ast.left)} {ast.op} {_operand(ast.right)}"


def operators_used(ast):
    found = set()

    def walk(n):
        if isinstance(n, Not):
            found.add("NOT"); walk(n.operand)
        elif isinstance(n, BinOp):
            found.add(n.op); walk(n.left); walk(n.right)

    walk(ast)
    return [op for op in ("NOT", "AND", "XOR", "OR") if op in found]


def _meaning(n):
    if isinstance(n, Not):
        return f"NOT gate: flips {_operand(n.operand)} (0 becomes 1, 1 becomes 0)."
    l, r = _operand(n.left), _operand(n.right)
    return {
        "AND": f"AND gate: 1 only when both {l} and {r} are 1.",
        "OR": f"OR gate: 1 when {l} or {r} (or both) is 1.",
        "XOR": f"XOR gate: 1 when {l} and {r} are different.",
    }[n.op]


def explain(ast):
    """Rule-based explanation: summary sentence plus gate-by-gate steps (inner gates first)."""
    steps, seen = [], set()

    def walk(n):
        if isinstance(n, (Var, Const)):
            return
        if isinstance(n, Not):
            walk(n.operand)
        else:
            walk(n.left); walk(n.right)
        key = to_string(n)
        if key not in seen:
            seen.add(key)
            steps.append({"expression": key, "meaning": _meaning(n)})

    walk(ast)
    if isinstance(ast, Var):
        summary = f"The output simply follows input {ast.name}."
    elif isinstance(ast, Const):
        summary = f"The output is the constant {ast.value}."
    elif isinstance(ast, Not):
        summary = f"The final gate is a NOT gate inverting {_operand(ast.operand)}."
    else:
        summary = (f"The final gate is a {ast.op} gate combining "
                   f"{_operand(ast.left)} and {_operand(ast.right)}.")
    return {"summary": summary, "steps": steps}
