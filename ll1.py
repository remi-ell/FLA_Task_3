"""
FIRST / FOLLOW sets, LL(1) table and a table-driven predictive parser.

A predictive parser is a deterministic PDA that may peek at one input token.
Printing its stack after every move shows the stack moves step by step.
"""
from .grammar import EPS

END = "$"


def first_follow(cfg):
    first = {A: set() for A in cfg.nonterminals}

    def first_of(seq):
        out = set()
        for s in seq:
            f = {s} if s in cfg.terminals else first[s]
            out |= f - {EPS}
            if EPS not in f:
                return out
        return out | {EPS}

    changed = True
    while changed:
        changed = False
        for A, rhss in cfg.prods.items():
            for r in rhss:
                f = first_of(r)
                if not f <= first[A]:
                    first[A] |= f
                    changed = True
    follow = {A: set() for A in cfg.nonterminals}
    follow[cfg.start].add(END)
    changed = True
    while changed:
        changed = False
        for A, rhss in cfg.prods.items():
            for r in rhss:
                for k, B in enumerate(r):
                    if B not in cfg.nonterminals:
                        continue
                    f = first_of(r[k + 1:])
                    add = (f - {EPS}) | (follow[A] if EPS in f else set())
                    if not add <= follow[B]:
                        follow[B] |= add
                        changed = True
    return first, follow, first_of


def ll1_table(cfg):
    """Returns (table, conflicts, first, follow). table[(A, a)] is the list of
    productions predicted for nonterminal A on look-ahead a; a cell with more
    than one production is a conflict."""
    first, follow, first_of = first_follow(cfg)
    table = {}
    for A, rhss in cfg.prods.items():
        for r in rhss:
            f = first_of(r)
            for a in (f - {EPS}) | (follow[A] if EPS in f else set()):
                cell = table.setdefault((A, a), [])
                if r not in cell:
                    cell.append(r)
    conflicts = sorted(k for k, v in table.items() if len(v) > 1)
    return table, conflicts, first, follow


def predictive_parse(cfg, tokens, prefer=None):
    """Table-driven LL(1) parse. `prefer` resolves a conflict cell:
    {(A, a): rhs} picks that production (e.g. 'shift' the else).
    Returns (accepted, steps); a step is (stack with top on the left, input, action)."""
    table, conflicts, _, _ = ll1_table(cfg)
    prefer = prefer or {}
    unresolved = [c for c in conflicts if c not in prefer]
    if unresolved:
        raise ValueError(f"{cfg.name} is not LL(1): conflicts at {unresolved}")
    stack = [END, cfg.start]
    toks = list(tokens) + [END]
    i, steps = 0, []

    def snapshot():
        return " ".join(reversed(stack)), " ".join(toks[i:])

    while True:
        top, a = stack[-1], toks[i]
        st, inp = snapshot()
        if top == END and a == END:
            steps.append((st, inp, "accept"))
            return True, steps
        if top == END or top in cfg.terminals:
            if top == a:
                steps.append((st, inp, f"match {a}"))
                stack.pop()
                i += 1
                continue
            steps.append((st, inp, f"error: expected {top}, found {a}"))
            return False, steps
        cell = table.get((top, a))
        if not cell:
            steps.append((st, inp, f"error: M[{top}, {a}] is empty"))
            return False, steps
        rhs = prefer.get((top, a), cell[0])
        steps.append((st, inp, f"{top} → {' '.join(rhs) if rhs else EPS}"))
        stack.pop()
        stack.extend(reversed(rhs))
