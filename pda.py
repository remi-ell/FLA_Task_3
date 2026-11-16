"""
Pushdown automata for Task 3.

An instantaneous description (ID) is (q, w, γ): state, unread input and stack,
with the stack TOP ON THE LEFT, written exactly as in the textbook.
The simulator explores IDs breadth first, so it also handles nondeterministic
PDAs, and it can print the moves of one accepting computation.
"""
from collections import deque

EPS = "ε"


class PDA:
    def __init__(self, name, states, sigma, gamma, delta, start, bottom,
                 final=(), accept_by="final"):
        """
        delta: {(state, input symbol or EPS, stack top): [(next state, push), ...]}
               push is a tuple of stack symbols, leftmost = new top; () pops.
        accept_by: "final" (final state, all input read) or "empty" (empty stack).
        """
        self.name = name
        self.states = list(states)
        self.sigma = list(sigma)
        self.gamma = list(gamma)
        self.delta = {k: [(q, tuple(p)) for q, p in v] for k, v in delta.items()}
        self.start = start
        self.bottom = bottom
        self.final = set(final)
        self.accept_by = accept_by
        self.min_need = None     # optional: stack symbol -> least input it must still consume

    # ---------------------------------------------------------- determinism
    def choice_points(self):
        """Every place where the PDA has more than one possible move."""
        found = []
        for (q, a, X), moves in self.delta.items():
            if len(moves) > 1:
                found.append((q, a, X, f"{len(moves)} moves for the same (q, a, X)"))
            if a == EPS:
                for b in self.sigma:
                    if (q, b, X) in self.delta:
                        found.append((q, b, X, "an ε-move competes with an input move"))
        return found

    def is_deterministic(self):
        return not self.choice_points()

    # ------------------------------------------------------------ simulation
    def run(self, tokens, max_ids=500000):
        """Breadth-first search over IDs.
        Returns {"accepted", "path" (IDs of one accepting run, or of the
        furthest run when rejected), "explored" (IDs taken off the queue)}."""
        toks = list(tokens)
        n = len(toks)
        first = (self.start, 0, (self.bottom,))
        parent = {first: None}
        todo = deque([first])
        explored, best, hit = 0, first, None
        while todo and explored < max_ids:
            cfg = todo.popleft()
            explored += 1
            q, i, stack = cfg
            if (i, -len(stack)) > (best[1], -len(best[2])):
                best = cfg
            if self._accepts(cfg, n):
                hit = cfg
                break
            if not stack:
                continue
            top = stack[0]
            moves = []
            if i < n:
                moves += [(p, i + 1, push) for p, push in self.delta.get((q, toks[i], top), [])]
            moves += [(p, i, push) for p, push in self.delta.get((q, EPS, top), [])]
            for p, j, push in moves:
                new_stack = push + stack[1:]
                if self.min_need and sum(self.min_need.get(s, 0) for s in new_stack) > n - j:
                    continue          # the stack needs more input than is left
                nxt = (p, j, new_stack)
                if nxt not in parent:
                    parent[nxt] = cfg
                    todo.append(nxt)
        end = hit or best
        path = []
        while end is not None:
            path.append(end)
            end = parent[end]
        path.reverse()
        return {"accepted": hit is not None, "explored": explored,
                "path": [(q, "".join(toks[i:]) if all(len(t) == 1 for t in toks)
                          else " ".join(toks[i:]), "".join(s)) for q, i, s in path]}

    def _accepts(self, cfg, n):
        q, i, stack = cfg
        if i != n:
            return False
        return q in self.final if self.accept_by == "final" else not stack

    def accepts(self, tokens):
        return self.run(tokens)["accepted"]

    # -------------------------------------------------------------- display
    @staticmethod
    def show_id(q, w, stack):
        return f"({q},{w or EPS},{stack or EPS})"

    def show_run(self, path):
        return " ⊢ ".join(self.show_id(*p) for p in path)

    def transitions_text(self):
        def word(push):
            sep = "" if all(len(s) == 1 for s in push) else " "
            return sep.join(push) or EPS
        return [f"δ({q}, {a}, {X}) = {{" + ", ".join(f"({p}, {word(push)})" for p, push in moves) + "}"
                for (q, a, X), moves in self.delta.items()]

    def to_dot(self, labels=None):
        """labels: optional {(q, p): [edge text, ...]} to draw compact edges."""
        out = [f'digraph "{self.name}" {{', "  rankdir=LR; bgcolor=white;",
               '  node [shape=circle fontname="Helvetica" fontsize=12];',
               '  edge [fontname="Helvetica" fontsize=10];',
               "  start [shape=point width=0.08];"]
        for q in self.states:
            out.append(f'  "{q}" [shape={"doublecircle" if q in self.final else "circle"}];')
        out.append(f'  start -> "{self.start}";')
        if labels is None:
            labels = {}
            for (q, a, X), moves in self.delta.items():
                for p, push in moves:
                    labels.setdefault((q, p), []).append(f"{a}, {X} / {''.join(push) or EPS}")
        for (q, p), texts in labels.items():
            out.append(f'  "{q}" -> "{p}" [label="' + "\\l".join(texts) + '\\l"];')
        out.append("}")
        return "\n".join(out)


def cfg_to_pda(cfg, name=None):
    """Standard CFG -> PDA construction (Hopcroft, Motwani and Ullman):
    one state q, accept by empty stack;
      δ(q, ε, A) contains (q, β) for every production A -> β,
      δ(q, a, a) = {(q, ε)} for every terminal a."""
    delta = {}
    for A, rhss in cfg.prods.items():
        delta[("q", EPS, A)] = [("q", tuple(r)) for r in rhss]
    for a in sorted(cfg.terminals):
        delta[("q", a, a)] = [("q", ())]
    pda = PDA(name or f"PDA for {cfg.name}", ["q"], sorted(cfg.terminals),
              sorted(cfg.nonterminals) + sorted(cfg.terminals), delta, "q", cfg.start,
              accept_by="empty")
    pda.min_need = {**{a: 1 for a in cfg.terminals}, **cfg.min_len}
    return pda
