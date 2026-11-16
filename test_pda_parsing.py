"""
28 checks for the Task 3 case studies. Every machine is compared with an
independent checker: Python's json and ast parsers, a counting rule, and
plain arithmetic on string lengths.
"""
import json
import random
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pda_parsing.cases import (  # noqa: E402
    BOOL_PDA, BOOL_STRINGS, CODE_LINES, G1, G1_REVISED, G2, G2_LL1, G2_REVISED, G3,
    G3_REVISED, G4, G4_REVISED, LEDGER_DPDA, LEDGER_STRINGS, LIST_DPDA, LIST_STRINGS,
    MARKED_STRINGS, ONE_TWO_DPDA, ONE_TWO_NPDA, ONE_TWO_STRINGS, bool_value, list_tokens,
    python_bool_valid)
from pda_parsing.ll1 import ll1_table, predictive_parse  # noqa: E402


def all_strings(symbols, max_len):
    for n in range(max_len + 1):
        for t in product(symbols, repeat=n):
            yield list(t)


def json_list_oracle(tokens):
    """Python's json module decides: x -> 0, and the top level must be a list."""
    try:
        return isinstance(json.loads("".join("0" if t == "x" else t for t in tokens)), list)
    except ValueError:
        return False


# ======================================================= 1. list literals
def test_list_listed_strings():                                       # 1
    for s in LIST_STRINGS["accept"]:
        assert G1_REVISED.derives(list(s)) and LIST_DPDA.accepts(list(s)), s
    for s in LIST_STRINGS["reject"]:
        assert not G1_REVISED.derives(list(s)) and not LIST_DPDA.accepts(list(s)), s


def test_lists_exhaustive_against_json():                             # 2
    """All 349 525 token strings up to length 9 over { [ ] , x }."""
    count = 0
    for t in all_strings(["[", "]", ",", "x"], 9):
        count += 1
        ref = json_list_oracle(t)
        assert LIST_DPDA.accepts(t) == ref, t
        assert G1_REVISED.derives(t) == ref, t
        assert G1.derives(t) == ref, t
        assert predictive_parse(G1_REVISED, t)[0] == ref, t
    assert count == 349525


def test_list_tree_counts_are_catalan():                              # 3
    counts = [G1.count_parse_trees(list("[" + ",".join("x" * k) + "]")) for k in range(1, 7)]
    assert counts == [1, 1, 2, 5, 14, 42]
    assert all(G1_REVISED.count_parse_trees(list("[" + ",".join("x" * k) + "]")) == 1
               for k in range(1, 7))


def test_list_grammars_same_language_and_unambiguous():               # 4
    old, new = G1.strings_up_to(11), G1_REVISED.strings_up_to(11)
    assert old == new
    assert all(G1_REVISED.count_parse_trees(s) == 1 for s in new)


def test_list_dpda_deterministic_and_ll1():                           # 5
    assert LIST_DPDA.is_deterministic()
    assert ll1_table(G1_REVISED)[1] == [] and len(ll1_table(G1)[1]) == 3


def test_list_syntax_checker():                                       # 6
    for line in CODE_LINES["accept"]:
        assert LIST_DPDA.accepts(list_tokens(line)), line
    for line in CODE_LINES["reject"]:
        assert not LIST_DPDA.accepts(list_tokens(line)), line


def test_list_stack_moves_match_report():                             # 7
    run = LIST_DPDA.run(list("[[x],x]"))
    assert LIST_DPDA.show_run(run["path"]) == (
        "(q0,[[x],x],Z) ⊢ (q1,[x],x],[Z) ⊢ (q1,x],x],[[Z) ⊢ (q2,],x],[[Z) ⊢ "
        "(q2,,x],[Z) ⊢ (q3,x],[Z) ⊢ (q2,],[Z) ⊢ (q2,ε,Z) ⊢ (qf,ε,Z)")
    run = LIST_DPDA.run(list("[x,]"))
    assert not run["accepted"] and run["path"][-1] == ("q3", "]", "[Z")


# ================================================== 2. Boolean expressions
def test_bool_listed_strings():                                       # 8
    for s in BOOL_STRINGS["accept"]:
        t = G2.tokenize(s)
        assert G2_REVISED.derives(t) and BOOL_PDA.accepts(t) and predictive_parse(G2_LL1, t)[0], s
    for s in BOOL_STRINGS["reject"]:
        t = G2.tokenize(s)
        assert not (G2_REVISED.derives(t) or BOOL_PDA.accepts(t) or predictive_parse(G2_LL1, t)[0]), s


def test_bool_exhaustive_against_python():                            # 9
    """All 9 331 token strings up to length 5 over {p, not, and, or, (, )}."""
    count = 0
    for t in all_strings(["p", "not", "and", "or", "(", ")"], 5):
        count += 1
        ref = python_bool_valid(t)
        assert G2.derives(t) == ref and G2_REVISED.derives(t) == ref, t
        assert predictive_parse(G2_LL1, t)[0] == ref, t
    assert count == 9331


def test_bool_pda_random():                                           # 10
    rnd = random.Random(268)
    toks = ["p", "not", "and", "or", "(", ")"]
    for _ in range(1500):
        t = [rnd.choice(toks) for _ in range(rnd.randint(0, 7))]
        assert BOOL_PDA.accepts(t) == python_bool_valid(t), t


def test_bool_ambiguity_changes_truth_value():                        # 11
    trees = G2.trees(G2.tokenize("p or p and p"))
    assert sorted(bool_value(t, [True, False, False]) for t in trees) == [False, True]
    trees = G2.trees(G2.tokenize("not p and p"))
    assert sorted(bool_value(t, [True, False]) for t in trees) == [False, True]


def test_bool_precedence_matches_python():                            # 12
    """The single G2' tree evaluates like Python for every assignment."""
    for text in ["p or p and p", "not p and p", "not p or p and not p", "(p or p) and p"]:
        t = G2.tokenize(text)
        (tree,) = G2_REVISED.trees(t)
        n = t.count("p")
        for vals in product([False, True], repeat=n):
            it = iter(vals)
            src = " ".join(str(next(it)) if x == "p" else x for x in t)
            assert bool_value(tree, list(vals)) == eval(src), (text, vals)  # noqa: S307


def test_bool_ll1_conflicts():                                        # 13
    assert [len(ll1_table(g)[1]) for g in (G2, G2_REVISED, G2_LL1)] == [3, 6, 0]


def test_bool_first_follow():                                         # 14
    _, _, first, follow = ll1_table(G2_LL1)
    assert first["B"] == first["T"] == first["F"] == {"not", "(", "p"}
    assert follow["B"] == {")", "$"} and follow["T"] == {"or", ")", "$"}


def test_bool_pda_nondeterministic_50_configs():                      # 15
    assert not BOOL_PDA.is_deterministic()
    run = BOOL_PDA.run(G2.tokenize("p or p and p"))
    assert run["accepted"] and run["explored"] == 50


def test_bool_parser_17_steps():                                      # 16
    ok, steps = predictive_parse(G2_LL1, G2.tokenize("p or p and p"))
    assert ok and len(steps) == 17


# ============================================================ 3. ledger
def test_ledger_listed_strings():                                     # 17
    for s in LEDGER_STRINGS["accept"]:
        assert LEDGER_DPDA.accepts(list(s)) and G3_REVISED.derives(list(s)), s
    for s in LEDGER_STRINGS["reject"]:
        assert not LEDGER_DPDA.accepts(list(s)) and not G3_REVISED.derives(list(s)), s


def test_ledger_exhaustive_counting_rule():                           # 18
    """All 8 191 strings up to length 12 over {a, b}."""
    count = 0
    for s in all_strings("ab", 12):
        count += 1
        ref = s.count("a") == s.count("b")
        assert LEDGER_DPDA.accepts(s) == ref, s
        assert G3_REVISED.derives(s) == ref and G3.derives(s) == ref, s
    assert count == 8191


def test_ledger_ambiguity():                                          # 19
    assert [G3.count_parse_trees(list("ab" * k)) for k in range(1, 6)] == [1, 2, 5, 14, 42]
    assert all(G3_REVISED.count_parse_trees(s) == 1 for s in G3_REVISED.strings_up_to(10))


def test_ledger_dpda_deterministic():                                 # 20
    assert LEDGER_DPDA.is_deterministic() and LEDGER_DPDA.states == ["q0", "q1"]


def test_ledger_stack_moves_match_report():                           # 21
    run = LEDGER_DPDA.run(list("abba"))
    assert LEDGER_DPDA.show_run(run["path"]) == (
        "(q0,abba,Z) ⊢ (q1,bba,CZ) ⊢ (q1,ba,Z) ⊢ (q0,ba,Z) ⊢ (q1,a,DZ) ⊢ (q1,ε,Z) ⊢ (q0,ε,Z)")


# =================================================== 4. a^n b^n ∪ a^n b^2n
def one_two_rule(s):
    n = len(s) - len(s.lstrip("a"))
    rest = s[n:]
    return set(rest) <= {"b"} and len(rest) in (n, 2 * n)


def test_one_two_listed_strings():                                    # 22
    for s in ONE_TWO_STRINGS["accept"]:
        assert ONE_TWO_NPDA.accepts(list(s)) and G4_REVISED.derives(list(s)), s
    for s in ONE_TWO_STRINGS["reject"]:
        assert not ONE_TWO_NPDA.accepts(list(s)) and not G4_REVISED.derives(list(s)), s
    for s in MARKED_STRINGS["accept"]:
        assert ONE_TWO_DPDA.accepts(list(s)), s
    for s in MARKED_STRINGS["reject"]:
        assert not ONE_TWO_DPDA.accepts(list(s)), s


def test_one_two_exhaustive():                                        # 23
    """All 8 191 strings up to length 12 over {a, b}."""
    count = 0
    for t in all_strings("ab", 12):
        count += 1
        s = "".join(t)
        ref = one_two_rule(s)
        assert ONE_TWO_NPDA.accepts(t) == ref, s
        assert G4.derives(t) == ref and G4_REVISED.derives(t) == ref, s
    assert count == 8191


def test_marked_version_exhaustive():                                 # 24
    """All 21 845 strings up to length 7 over {a, b, c, d}."""
    count = 0
    for t in all_strings("abcd", 7):
        count += 1
        s = "".join(t)
        n = len(s) - len(s.lstrip("a"))
        rest = s[n:]
        ref = (rest[:1] == "c" and rest[1:] == "b" * n) or (rest[:1] == "d" and rest[1:] == "b" * 2 * n)
        assert ONE_TWO_DPDA.accepts(t) == ref, s
    assert count == 21845


def test_one_two_determinism():                                       # 25
    assert not ONE_TWO_NPDA.is_deterministic()
    assert ONE_TWO_DPDA.is_deterministic()


def test_one_two_ambiguous_only_on_empty_string():                    # 26
    strings = G4.strings_up_to(12)
    assert [s for s in strings if G4.count_parse_trees(s) > 1] == [()]
    assert all(G4_REVISED.count_parse_trees(s) == 1 for s in strings)
    assert G4_REVISED.strings_up_to(12) == strings


# ============================================================== general
def test_pumping_lemma_for_lists():                                   # 27
    """[^p ]^p : every split xyz with |xy| <= p, |y| >= 1 pumps out of the language."""
    for p in range(1, 9):
        s = "[" * p + "]" * p
        for i in range(p):
            for j in range(i + 1, p + 1):
                x, y, z = s[:i], s[i:j], s[j:]
                assert not LIST_DPDA.accepts(list(x + y * 2 + z))


def test_npda_guess_explores_both_branches():                         # 28
    run = ONE_TWO_NPDA.run(list("aabbbb"))
    assert run["accepted"] and run["path"][1][0] == "p2"
    run = ONE_TWO_NPDA.run(list("aabb"))
    assert run["accepted"] and run["path"][1][0] == "p1"
