"""
The four Task 3 case studies.

  1. Nested list literals   - JSON-style arrays [x, [x, x], []]; ambiguous item list
                              fixed; 5-state DPDA used as a syntax checker
  2. Boolean expressions    - not / and / or precedence ambiguity, CFG -> PDA, LL(1)
  3. Credit/debit ledger    - equal numbers of a and b in any order; ambiguous
                              grammar fixed; 2-state counting DPDA
  4. One or two per item    - a^n b^n  ∪  a^n b^2n: NPDA that guesses, versus a
                              DPDA when a marker says which case applies
"""
import ast

from .grammar import CFG
from .pda import EPS, PDA, cfg_to_pda

# =========================================================================
# 1. Nested list literals over  [  ]  ,  x
# =========================================================================
LIST_T = {"[", "]", ",", "x"}

G1 = CFG("G1 lists (ambiguous)", "L",
         {"L": [["[", "]"], ["[", "I", "]"]],
          "I": [["I", ",", "I"], ["V"]],
          "V": [["x"], ["L"]]},
         LIST_T)

G1_REVISED = CFG("G1' lists (revised, LL(1))", "L",
                 {"L": [["[", "R"]],
                  "R": [["]"], ["V", "M"]],
                  "M": [[",", "V", "M"], ["]"]],
                  "V": [["x"], ["L"]]},
                 LIST_T)


def _list_dpda():
    """q0 start, q1 just opened (value or ']'), q2 after a value (',' or ']'),
    q3 after ',' (value), qf the outermost list is closed."""
    d = {("q0", "[", "Z"): [("q1", ("[", "Z"))],
         ("q1", "[", "["): [("q1", ("[", "["))],
         ("q1", "x", "["): [("q2", ("[",))],
         ("q1", "]", "["): [("q2", ())],
         ("q2", ",", "["): [("q3", ("[",))],
         ("q2", "]", "["): [("q2", ())],
         ("q3", "[", "["): [("q1", ("[", "["))],
         ("q3", "x", "["): [("q2", ("[",))],
         ("q2", EPS, "Z"): [("qf", ("Z",))]}
    return PDA("M1: DPDA for list literals", ["q0", "q1", "q2", "q3", "qf"], ["[", "]", ",", "x"],
               ["[", "Z"], d, "q0", "Z", final={"qf"})


LIST_DPDA = _list_dpda()


def list_tokens(text):
    """Lexer for the syntax checker: brackets and commas stay, every number,
    string literal or word becomes one value token x, white space is skipped."""
    out, k = [], 0
    while k < len(text):
        ch = text[k]
        if ch in "[],":
            out.append(ch)
            k += 1
        elif ch.isspace():
            k += 1
        elif ch in "\"'":
            end = text.find(ch, k + 1)
            out.append("x")
            k = len(text) if end < 0 else end + 1
        else:
            while k < len(text) and text[k] not in "[], \t\"'":
                k += 1
            out.append("x")
    return out


CODE_LINES = {
    "accept": ['[1, 2, 3]', '[[1, 2], [3, 4], []]', '["srm", ["trichy", 621105]]',
               '[[], [[]], [[[]]]]', '[true, null, "a,b"]'],
    "reject": ['[1, 2,]', '[1 2]', '[[1, 2]', '1, 2', '[,]', '[]]'],
}

LIST_STRINGS = {
    "accept": ["[]", "[x]", "[x,x]", "[[x],x]", "[[],[x,[x]]]", "[x,[],x]"],
    "reject": ["", "x", "[x,]", "[,x]", "[x x]", "[[x]", "[]]"],
}

# =========================================================================
# 2. Boolean expressions over  p  not  and  or  ( )
# =========================================================================
BOOL_T = {"p", "not", "and", "or", "(", ")"}

G2 = CFG("G2 Boolean (ambiguous)", "B",
         {"B": [["B", "or", "B"], ["B", "and", "B"], ["not", "B"], ["(", "B", ")"], ["p"]]},
         BOOL_T)

G2_REVISED = CFG("G2' Boolean (precedence levels)", "B",
                 {"B": [["B", "or", "T"], ["T"]],
                  "T": [["T", "and", "F"], ["F"]],
                  "F": [["not", "F"], ["(", "B", ")"], ["p"]]},
                 BOOL_T)

G2_LL1 = CFG("G2'' Boolean (left recursion removed, LL(1))", "B",
             {"B": [["T", "B'"]],
              "B'": [["or", "T", "B'"], []],
              "T": [["F", "T'"]],
              "T'": [["and", "F", "T'"], []],
              "F": [["not", "F"], ["(", "B", ")"], ["p"]]},
             BOOL_T)

BOOL_PDA = cfg_to_pda(G2_REVISED, "PDA from G2' (one state, empty stack)")

BOOL_STRINGS = {
    "accept": ["p", "p or p and p", "not p and p", "(p or p) and not p", "not not p",
               "p and (p or not (p))"],
    "reject": ["", "p or", "and p", "p not p", "(p or p", "p and or p", "not"],
}


def bool_value(tree, values):
    """Evaluate a Boolean parse tree; the k-th p takes values[k]."""
    it = iter(values)

    def ev(node):
        sym, kids, _ = node
        if not kids:
            return next(it) if sym == "p" else sym
        parts = [ev(k) for k in kids if k[0] != "ε"]
        names = [k[0] for k in kids]
        if names[0] == "not":
            return not parts[1]
        if names[0] == "(":
            return parts[1]
        if len(parts) == 1:
            return parts[0]
        a, op, b = parts
        return (a or b) if op == "or" else (a and b)
    return ev(tree)


def python_bool_valid(tokens):
    """Independent oracle: Python's parser on the same tokens (p -> True)."""
    if not tokens:
        return False
    src = " ".join("True" if t == "p" else t for t in tokens)
    try:
        tree = ast.parse(src, mode="eval")
    except SyntaxError:
        return False
    allowed = (ast.Expression, ast.BoolOp, ast.UnaryOp, ast.Not, ast.And, ast.Or, ast.Constant)
    return all(isinstance(n, allowed) for n in ast.walk(tree))


# =========================================================================
# 3. Credit / debit ledger: equal numbers of a (credit) and b (debit)
# =========================================================================
G3 = CFG("G3 ledger (ambiguous)", "S",
         {"S": [["a", "S", "b", "S"], ["b", "S", "a", "S"], []]}, {"a", "b"})

G3_REVISED = CFG("G3' ledger (revised)", "S",
                 {"S": [["a", "B", "S"], ["b", "A", "S"], []],
                  "A": [["a"], ["b", "A", "A"]],
                  "B": [["b"], ["a", "B", "B"]]},
                 {"a", "b"})


def _ledger_dpda():
    """The stack holds the surplus: C per unmatched credit, D per unmatched debit."""
    d = {("q0", "a", "Z"): [("q1", ("C", "Z"))],
         ("q0", "b", "Z"): [("q1", ("D", "Z"))],
         ("q1", "a", "C"): [("q1", ("C", "C"))],
         ("q1", "a", "D"): [("q1", ())],
         ("q1", "b", "D"): [("q1", ("D", "D"))],
         ("q1", "b", "C"): [("q1", ())],
         ("q1", EPS, "Z"): [("q0", ("Z",))]}
    return PDA("M3: DPDA for a balanced ledger", ["q0", "q1"], ["a", "b"], ["C", "D", "Z"],
               d, "q0", "Z", final={"q0"})


LEDGER_DPDA = _ledger_dpda()

LEDGER_STRINGS = {
    "accept": ["", "ab", "ba", "abba", "baab", "aababb", "bbaa"],
    "reject": ["a", "b", "aab", "abb", "aaabb", "babbb"],
}

# =========================================================================
# 4. One or two per item:  a^n b^n  ∪  a^n b^2n
# =========================================================================
G4 = CFG("G4 a^n b^n ∪ a^n b^2n (ambiguous)", "S",
         {"S": [["S1"], ["S2"]],
          "S1": [["a", "S1", "b"], []],
          "S2": [["a", "S2", "b", "b"], []]},
         {"a", "b"})

G4_REVISED = CFG("G4' (revised)", "S",
                 {"S": [[], ["T1"], ["T2"]],
                  "T1": [["a", "T1", "b"], ["a", "b"]],
                  "T2": [["a", "T2", "b", "b"], ["a", "b", "b"]]},
                 {"a", "b"})


def _one_or_two_npda():
    """Guess at the start whether each a will be matched by one b (p1) or by
    two b's (p2: push two X per a)."""
    d = {("s", EPS, "Z"): [("p1", ("Z",)), ("p2", ("Z",))]}
    for state, push in (("p1", ("X",)), ("p2", ("X", "X"))):
        d[(state, "a", "Z")] = [(state, push + ("Z",))]
        d[(state, "a", "X")] = [(state, push + ("X",))]
        d[(state, "b", "X")] = [("r", ())]
        d[(state, EPS, "Z")] = [("f", ("Z",))]
    d[("r", "b", "X")] = [("r", ())]
    d[("r", EPS, "Z")] = [("f", ("Z",))]
    return PDA("NPDA for a^n b^n ∪ a^n b^2n", ["s", "p1", "p2", "r", "f"], ["a", "b"],
               ["X", "Z"], d, "s", "Z", final={"f"})


def _marked_dpda():
    """With a marker the guess is unnecessary: c means 'one b each', d means 'two b each'.
    Language { a^n c b^n } ∪ { a^n d b^2n }."""
    d = {}
    for X in ("Z", "X"):
        d[("p", "a", X)] = [("p", ("X", X))]
        d[("p", "c", X)] = [("one", (X,))]
        d[("p", "d", X)] = [("two", (X,))]
    d[("one", "b", "X")] = [("one", ())]
    d[("two", "b", "X")] = [("half", ("X",))]      # first b of a pair: keep the X
    d[("half", "b", "X")] = [("two", ())]          # second b: now pop it
    d[("one", EPS, "Z")] = [("f", ("Z",))]
    d[("two", EPS, "Z")] = [("f", ("Z",))]
    return PDA("DPDA for a^n c b^n ∪ a^n d b^2n", ["p", "one", "two", "half", "f"],
               ["a", "b", "c", "d"], ["X", "Z"], d, "p", "Z", final={"f"})


ONE_TWO_NPDA = _one_or_two_npda()
ONE_TWO_DPDA = _marked_dpda()

ONE_TWO_STRINGS = {
    "accept": ["", "ab", "abb", "aabb", "aabbbb", "aaabbb"],
    "reject": ["a", "b", "aab", "abbb", "aabbb", "ba"],
}
MARKED_STRINGS = {
    "accept": ["c", "d", "acb", "adbb", "aacbb", "aadbbbb"],
    "reject": ["", "ab", "acbb", "adb", "aadbbb", "ca"],
}

ALL_GRAMMARS = [(G1, 11), (G1_REVISED, 11), (G2, 7), (G2_REVISED, 7), (G2_LL1, 7),
                (G3, 10), (G3_REVISED, 10), (G4, 12), (G4_REVISED, 12)]
