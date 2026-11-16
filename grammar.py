"""
Context-free grammars for Task 3.

Parse trees are counted with a memoised span table (a CYK-style dynamic
programme that works directly on the grammar, epsilon rules included), so
even the ambiguous grammars can be checked on thousands of strings quickly.
The same table enumerates the trees themselves, from which leftmost and
rightmost derivations are read off.

Restriction (true for every grammar in this repo): no unit/epsilon cycles,
i.e. no nonterminal can derive itself without consuming input.
"""
import re
from collections import Counter
from functools import lru_cache

EPS = "ε"


class CFG:
    def __init__(self, name, start, productions, terminals):
        """productions: {A: [rhs, ...]}, each rhs a list of symbols, [] = ε."""
        self.name = name
        self.start = start
        self.prods = {a: [list(r) for r in rhss] for a, rhss in productions.items()}
        self.terminals = set(terminals)
        self.nonterminals = set(self.prods)
        self.min_len = self._min_yield()

    # ------------------------------------------------------------- basics
    def _min_yield(self):
        big = 10 ** 9
        m = {a: big for a in self.nonterminals}
        changed = True
        while changed:
            changed = False
            for a, rhss in self.prods.items():
                for r in rhss:
                    v = sum(1 if s in self.terminals else m[s] for s in r)
                    if v < m[a]:
                        m[a], changed = v, True
        return m

    def cost(self, symbols):
        return sum(1 if s in self.terminals else self.min_len[s] for s in symbols)

    def tokenize(self, text):
        """Split text into terminals, longest match first; spaces are ignored."""
        terms = sorted(self.terminals, key=len, reverse=True)
        return re.findall("|".join(re.escape(t) for t in terms) + r"|\S", text)

    def productions_text(self):
        return [f"{a} → " + " | ".join(" ".join(r) if r else EPS for r in rhss)
                for a, rhss in self.prods.items()]

    # ------------------------------------------------------ counting trees
    def _tables(self, tokens):
        toks = tuple(tokens)
        n = len(toks)

        @lru_cache(maxsize=None)
        def sym(X, i, j):
            if X in self.terminals:
                return 1 if j == i + 1 and toks[i] == X else 0
            return sum(seq(tuple(r), i, j) for r in self.prods[X])

        @lru_cache(maxsize=None)
        def seq(rhs, i, j):
            if not rhs:
                return 1 if i == j else 0
            if j - i < self.cost(rhs):
                return 0
            head, rest = rhs[0], rhs[1:]
            hi = j - self.cost(rest)
            total = 0
            for k in range(i + (1 if head in self.terminals else self.min_len[head]), hi + 1):
                left = sym(head, i, k)
                if left:
                    total += left * seq(rest, k, j)
            return total
        return sym, seq, n

    def count_parse_trees(self, tokens):
        sym, _, n = self._tables(tokens)
        return sym(self.start, 0, n)

    def derives(self, tokens):
        return self.count_parse_trees(tokens) > 0

    def trees(self, tokens, limit=50):
        """Enumerate up to `limit` parse trees. A tree node is (symbol, children, position);
        leaves carry the index of their token, an ε-leaf has position None."""
        sym, seq, n = self._tables(tokens)

        def gen_sym(X, i, j):
            if X in self.terminals:
                yield (X, [], i)
                return
            for r in self.prods[X]:
                if not seq(tuple(r), i, j):
                    continue
                if not r:
                    yield (X, [(EPS, [], None)], None)
                    continue
                for kids in gen_seq(tuple(r), i, j):
                    yield (X, kids, None)

        def gen_seq(rhs, i, j):
            if not rhs:
                if i == j:
                    yield []
                return
            head, rest = rhs[0], rhs[1:]
            for k in range(i, j + 1):
                if sym(head, i, k) and seq(rest, k, j):
                    for left in gen_sym(head, i, k):
                        for right in gen_seq(rest, k, j):
                            yield [left] + right
        out = []
        if sym(self.start, 0, n):
            for t in gen_sym(self.start, 0, n):
                out.append(t)
                if len(out) >= limit:
                    break
        return out

    # --------------------------------------------------------- derivations
    def leftmost(self, tree):
        """Sentential forms of the leftmost derivation that builds `tree`."""
        return self._derivation(tree, leftmost=True)

    def rightmost(self, tree):
        return self._derivation(tree, leftmost=False)

    def _derivation(self, tree, leftmost):
        forms = [[tree]]
        while True:
            cur = forms[-1]
            idx = [k for k, node in enumerate(cur) if node[0] in self.nonterminals]
            if not idx:
                break
            k = idx[0] if leftmost else idx[-1]
            kids = [c for c in cur[k][1] if c[0] != EPS]
            forms.append(cur[:k] + kids + cur[k + 1:])
        return [[node[0] for node in f] for f in forms]

    @staticmethod
    def show_form(form):
        return " ".join(form) if form else EPS

    # -------------------------------------------------- generated strings
    def strings_up_to(self, max_len):
        """Every terminal string of length <= max_len the grammar generates."""
        out, seen, frontier = set(), set(), [(self.start,)]
        while frontier:
            nxt = []
            for form in frontier:
                if form in seen or self.cost(form) > max_len:
                    continue
                seen.add(form)
                j = next((k for k, s in enumerate(form) if s in self.nonterminals), None)
                if j is None:
                    out.add(form)
                    continue
                for r in self.prods[form[j]]:
                    nxt.append(form[:j] + tuple(r) + form[j + 1:])
            frontier = nxt
        return out

    def ambiguity_report(self, max_len):
        """Bounded ambiguity check. CFG ambiguity is undecidable in general, so
        counting the trees of every short string is evidence, not a proof."""
        counts, worst = Counter(), None
        for s in sorted(self.strings_up_to(max_len), key=lambda t: (len(t), t)):
            c = self.count_parse_trees(s)
            counts[c] += 1
            if c > 1 and (worst is None or c > worst[1]):
                worst = (" ".join(s), c)
        return counts, worst


def tree_to_dot(tree, title=""):
    lines = ["digraph T {", '  node [fontname="Helvetica" fontsize=12 shape=plaintext];',
             "  edge [arrowhead=none];"]
    if title:
        lines.append(f'  labelloc="t"; label="{title}"; fontname="Helvetica"; fontsize=13;')
    counter = [0]

    def walk(node):
        sym, kids, _ = node
        me = f"n{counter[0]}"
        counter[0] += 1
        colour = ' fontcolor="#1a5fb4"' if not kids else ""
        lines.append(f'  {me} [label="{sym}"{colour}];')
        for k in kids:
            lines.append(f"  {me} -> {walk(k)};")
        return me
    walk(tree)
    lines.append("}")
    return "\n".join(lines)
