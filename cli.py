"""
Terminal demo for the four Task 3 case studies.

  python -m pda_parsing.cli lists      nested list literals / syntax checker
  python -m pda_parsing.cli boolean    Boolean expressions (ambiguity, CFG -> PDA, LL(1))
  python -m pda_parsing.cli ledger     equal numbers of credits and debits
  python -m pda_parsing.cli onetwo     a^n b^n ∪ a^n b^2n (NPDA) vs marked version (DPDA)
  python -m pda_parsing.cli ambiguity  bounded ambiguity check of every grammar
  python -m pda_parsing.cli all        everything above (default)
"""
import sys

from .cases import (ALL_GRAMMARS, BOOL_PDA, BOOL_STRINGS, CODE_LINES, G1, G1_REVISED, G2,
                    G2_LL1, G2_REVISED, G3, G3_REVISED, G4, G4_REVISED, LEDGER_DPDA,
                    LEDGER_STRINGS, LIST_DPDA, LIST_STRINGS, MARKED_STRINGS, ONE_TWO_DPDA,
                    ONE_TWO_NPDA, ONE_TWO_STRINGS, bool_value, list_tokens, python_bool_valid)
from .grammar import EPS
from .ll1 import ll1_table, predictive_parse

COLOUR = sys.stdout.isatty() or "--color" in sys.argv
GREEN, RED, BOLD, DIM, END = ("\033[32m", "\033[31m", "\033[1m", "\033[2m", "\033[0m") \
    if COLOUR else ("",) * 5


def heading(text):
    print(f"\n{BOLD}{'=' * 74}\n{text}\n{'=' * 74}{END}")


def sub(text):
    print(f"\n{BOLD}-- {text}{END}")


def yes(ok):
    return f"{GREEN}ACCEPT{END}" if ok else f"{RED}REJECT{END}"


def pad(text, width):
    return text + " " * max(0, width - len(text.replace(GREEN, "").replace(RED, "").replace(END, "")))


def grammar(g):
    print(f"   {g.name}")
    for line in g.productions_text():
        print(f"     {line}")


def show_moves(pda, tokens):
    r = pda.run(tokens)
    print("   " + pda.show_run(r["path"]))
    return r


# ---------------------------------------------------------------------------
def lists():
    heading("CASE STUDY 1 - Nested list literals (syntax checker)")
    sub("Grammars")
    grammar(G1)
    grammar(G1_REVISED)
    sub("Parse trees of a list with k items (Catalan numbers in G1)")
    print(f"   {'string':<16}{'G1':>6}{'G1′':>6}")
    for k in range(1, 7):
        s = "[" + ",".join("x" * k) + "]"
        print(f"   {s:<16}{G1.count_parse_trees(list(s)):>6}{G1_REVISED.count_parse_trees(list(s)):>6}")
    sub("DPDA M1 (accepts by final state qf)")
    for line in LIST_DPDA.transitions_text():
        print("   " + line)
    print(f"   deterministic: {LIST_DPDA.is_deterministic()}")
    for s in ["[[x],x]", "[x,]"]:
        sub(f"Stack moves on {s} -> {yes(LIST_DPDA.accepts(list(s)))}")
        show_moves(LIST_DPDA, list(s))
    ok, steps = predictive_parse(G1_REVISED, list("[[x],x]"))
    print(f"\n   G1′ is LL(1): {ll1_table(G1_REVISED)[1] == []}; parser on [[x],x]: {yes(ok)} in {len(steps)} steps")
    sub("Test strings")
    for s in LIST_STRINGS["accept"] + LIST_STRINGS["reject"]:
        t = list(s)
        print(f"   {s or 'ε':<14} G1′: {yes(G1_REVISED.derives(t))}   M1: {yes(LIST_DPDA.accepts(t))}")
    sub("Syntax checker on JSON-style arrays (values become x)")
    for line in CODE_LINES["accept"] + CODE_LINES["reject"]:
        toks = list_tokens(line)
        print(f"   {yes(LIST_DPDA.accepts(toks))}  {line:<32}{DIM}{''.join(toks)}{END}")


def boolean():
    heading("CASE STUDY 2 - Boolean expressions")
    sub("Grammars")
    for g in (G2, G2_REVISED, G2_LL1):
        grammar(g)
    for text, vals in (("p or p and p", [True, False, False]), ("not p and p", [True, False])):
        w = G2.tokenize(text)
        sub(f"G2 on '{text}' with p = {', '.join('T' if v else 'F' for v in vals)}")
        for k, t in enumerate(G2.trees(w), 1):
            lmd = " ⇒ ".join(G2.show_form(f) for f in G2.leftmost(t))
            print(f"   LMD {k}: {lmd}   (value {bool_value(t, vals)})")
    w = G2.tokenize("p or p and p")
    t = G2_REVISED.trees(w)
    sub(f"G2′ on 'p or p and p': {len(t)} tree, value {bool_value(t[0], [True, False, False])}")
    print("   LMD: " + " ⇒ ".join(G2_REVISED.show_form(f) for f in G2_REVISED.leftmost(t[0])))
    sub("CFG → PDA construction from G2′")
    for line in BOOL_PDA.transitions_text():
        print("   " + line)
    r = BOOL_PDA.run(w)
    print(f"   deterministic: {BOOL_PDA.is_deterministic()}; configurations explored on "
          f"'p or p and p': {r['explored']} -> {yes(r['accepted'])}")
    sub("LL(1) conflicts per grammar")
    for g in (G2, G2_REVISED, G2_LL1):
        print(f"   {g.name:<48}{len(ll1_table(g)[1])} conflicting cell(s)")
    _, _, first, follow = ll1_table(G2_LL1)
    for A in G2_LL1.prods:
        print(f"   FIRST({A}) = {{{', '.join(sorted(first[A]))}}}   "
              f"FOLLOW({A}) = {{{', '.join(sorted(follow[A]))}}}")
    ok, steps = predictive_parse(G2_LL1, w)
    sub(f"Predictive parser on 'p or p and p' -> {yes(ok)} in {len(steps)} steps")
    print(f"   {'stack (top at left)':<24}{'input':<20}action")
    for st, inp, act in steps:
        print(f"   {st:<24}{inp:<20}{act}")
    sub("Test strings: CFG, PDA and LL(1) parser against Python's parser")
    print(f"   {'input':<24}{'G2′':<9}{'PDA':<9}{'LL(1)':<9}{'Python':<9}trees in G2")
    for s in BOOL_STRINGS["accept"] + BOOL_STRINGS["reject"]:
        t = G2.tokenize(s)
        print(f"   {s or 'ε':<24}{pad(yes(G2_REVISED.derives(t)), 9)}{pad(yes(BOOL_PDA.accepts(t)), 9)}"
              f"{pad(yes(predictive_parse(G2_LL1, t)[0]), 9)}{pad(yes(python_bool_valid(t)), 9)}"
              f"{G2.count_parse_trees(t)}")


def ledger():
    heading("CASE STUDY 3 - Credit/debit ledger (equal numbers of a and b)")
    grammar(G3)
    grammar(G3_REVISED)
    sub("Parse trees")
    print(f"   {'string':<10}{'G3':>5}{'G3′':>6}")
    for s in ["ab", "abab", "ababab", "abababab", "aabb", "abba"]:
        print(f"   {s:<10}{G3.count_parse_trees(list(s)):>5}{G3_REVISED.count_parse_trees(list(s)):>6}")
    t = G3_REVISED.trees(list("abba"))[0]
    print("   G3′ derivation of abba: " + " ⇒ ".join("".join(f) or EPS for f in G3_REVISED.leftmost(t)))
    sub("DPDA M3 (the stack stores the surplus)")
    for line in LEDGER_DPDA.transitions_text():
        print("   " + line)
    print(f"   deterministic: {LEDGER_DPDA.is_deterministic()}")
    for s in ["abba", "aab"]:
        sub(f"Stack moves on {s} -> {yes(LEDGER_DPDA.accepts(list(s)))}")
        show_moves(LEDGER_DPDA, list(s))
    sub("Test strings")
    for s in LEDGER_STRINGS["accept"] + LEDGER_STRINGS["reject"]:
        print(f"   {s or 'ε':<10} G3′: {yes(G3_REVISED.derives(list(s)))}   M3: {yes(LEDGER_DPDA.accepts(list(s)))}")


def onetwo():
    heading("CASE STUDY 4 - One or two per item: a^n b^n ∪ a^n b^2n")
    grammar(G4)
    grammar(G4_REVISED)
    print(f"   trees for ε: G4 {G4.count_parse_trees([])}, G4′ {G4_REVISED.count_parse_trees([])}")
    for pda in (ONE_TWO_NPDA, ONE_TWO_DPDA):
        sub(pda.name)
        for line in pda.transitions_text():
            print("   " + line)
        print(f"   deterministic: {pda.is_deterministic()}")
        for q, a, X, why in pda.choice_points()[:2]:
            print(f"   {DIM}choice at ({q}, {a}, {X}): {why}{END}")
    for pda, s in ((ONE_TWO_NPDA, "aabbbb"), (ONE_TWO_DPDA, "aadbbbb")):
        sub(f"{pda.name} on {s} -> {yes(pda.accepts(list(s)))}")
        show_moves(pda, list(s))
    sub("Test strings")
    for s in ONE_TWO_STRINGS["accept"] + ONE_TWO_STRINGS["reject"]:
        print(f"   {s or 'ε':<10} G4′: {yes(G4_REVISED.derives(list(s)))}   NPDA: {yes(ONE_TWO_NPDA.accepts(list(s)))}")
    for s in MARKED_STRINGS["accept"] + MARKED_STRINGS["reject"]:
        print(f"   {s or 'ε':<10} marked DPDA: {yes(ONE_TWO_DPDA.accepts(list(s)))}")


def ambiguity():
    heading("Bounded ambiguity check (parse trees of every short string)")
    print(f"   {'grammar':<46}{'len ≤':>6}{'strings':>9}{'>1 tree':>9}   worst case")
    for g, n in ALL_GRAMMARS:
        counts, worst = g.ambiguity_report(n)
        total = sum(counts.values())
        many = sum(v for k, v in counts.items() if k > 1)
        note = f"{RED}'{worst[0] or EPS}' has {worst[1]} trees{END}" if worst else f"{GREEN}one tree each{END}"
        print(f"   {g.name:<46}{n:>6}{total:>9}{many:>9}   {note}")
    print(f"   {DIM}Ambiguity is undecidable in general: this is evidence, not a proof.{END}")


def main(argv):
    args = [a for a in argv if a != "--color"] or ["all"]
    jobs = {"lists": lists, "boolean": boolean, "ledger": ledger, "onetwo": onetwo,
            "ambiguity": ambiguity}
    if args[0] == "all":
        for job in jobs.values():
            job()
        return 0
    if args[0] in jobs:
        jobs[args[0]]()
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
