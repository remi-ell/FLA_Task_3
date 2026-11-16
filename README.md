# Parsing Case Studies with Pushdown Automata and Context-Free Grammars

**Course:** 21CSC301T Formal Language and Automata, CLA-2, Assessment Task 3
**Student:** Remiel Debora E (RA2411026050268), rd4822@srmist.edu.in
**Faculty:** Dr. C. Gunasundari, Assistant Professor, Department of AIML, SRM IST Tiruchirappalli

| # | Case study | Ambiguous grammar → fix | PDA | Deterministic? |
|---|---|---|---|---|
| 1 | Nested list literals `[x, [x, x], []]` (JSON-style syntax checker) | `I → I , I` → right-recursive item list | 5-state DPDA | yes |
| 2 | Boolean expressions with `not`, `and`, `or` | one-level grammar → precedence levels B, T, F | CFG → PDA, LL(1) parser | general PDA no, LL(1) yes |
| 3 | Credit/debit ledger: equal numbers of a and b | `S → aSbS \| bSaS \| ε` → surplus grammar with A, B | 2-state counting DPDA | yes |
| 4 | One or two per item: aⁿbⁿ ∪ aⁿb²ⁿ | ambiguous only on ε → split ε off | NPDA (guess) vs DPDA with a marker | no / yes |

## Run it

```bash
pip install pytest
python -m pda_parsing.cli all          # every case study, derivations and stack moves
python -m pda_parsing.cli boolean      # or: lists | ledger | onetwo | ambiguity
python -m pytest -q                    # 28 checks
python tools/make_diagrams.py          # rebuild PDA diagrams and parse trees (Graphviz)
```

The package simulates PDAs over instantaneous descriptions (q, w, γ) with the stack top on
the left, checks determinism, converts CFGs to PDAs, counts parse trees with a span table and
builds FIRST/FOLLOW sets and LL(1) tables.

## 1. Nested list literals

Tokens `[ ] , x` (a lexer turns every number, word or string into `x`).
**G1:** `L → [ ] | [ I ]`, `I → I , I | V`, `V → x | L` is ambiguous: `I , I` does not say
how items group, so a list with k items has Catalan(k−1) trees (1, 1, 2, 5, 14, 42).
**G1′:** `L → [ R`, `R → ] | V M`, `M → , V M | ]`, `V → x | L` reads items left to right,
has one tree per string and is LL(1).

| G1, tree 1 of [x,x,x] | G1, tree 2 | G1′ |
|---|---|---|
| ![](docs/diagrams/tree_list_ambiguous_1.png) | ![](docs/diagrams/tree_list_ambiguous_2.png) | ![](docs/diagrams/tree_list_revised.png) |

**DPDA M1** (accept by final state qf): q1 = just opened, q2 = after a value, q3 = after a comma.

![](docs/diagrams/pda_lists.png)

```
[[x],x]: (q0,[[x],x],Z) ⊢ (q1,[x],x],[Z) ⊢ (q1,x],x],[[Z) ⊢ (q2,],x],[[Z) ⊢ (q2,,x],[Z)
         ⊢ (q3,x],[Z) ⊢ (q2,],[Z) ⊢ (q2,ε,Z) ⊢ (qf,ε,Z)   accept
[x,]:    (q0,[x,],Z) ⊢ (q1,x,],[Z) ⊢ (q2,,],[Z) ⊢ (q3,],[Z)   no move: ']' after ',' → reject
```

As a syntax checker it accepts `[[1, 2], [3, 4], []]` and `["srm", ["trichy", 621105]]` and
rejects `[1, 2,]`, `[1 2]` and `[[1, 2]`. The tests compare it with Python's `json` module on
all 349 525 token strings up to length 9.

## 2. Boolean expressions

**G2:** `B → B or B | B and B | not B | ( B ) | p`. With p = T, F, F, `p or p and p` is
**True** under one tree and **False** under the other; `not p and p` with p = T, F gives
False or True. **G2′:** `B → B or T | T`, `T → T and F | F`, `F → not F | ( B ) | p`
(not > and > or, as in Python and C).

| 'or' at the root (True) | 'and' at the root (False) | G2′ |
|---|---|---|
| ![](docs/diagrams/tree_bool_or_root.png) | ![](docs/diagrams/tree_bool_and_root.png) | ![](docs/diagrams/tree_bool_revised.png) |

The CFG → PDA construction gives a one-state nondeterministic PDA; it explores **50
configurations** to accept `p or p and p`. Without left recursion
(`B → T B'`, `B' → or T B' | ε`, `T → F T'`, `T' → and F T' | ε`, `F → not F | ( B ) | p`)
the LL(1) table has **0 conflicts** (G2 has 3, G2′ has 6) and the parser needs **17 steps**.

## 3. Credit/debit ledger

L = { w ∈ {a, b}* : #a(w) = #b(w) }: every credit a is balanced by a debit b, in any order.
**G3:** `S → aSbS | bSaS | ε` is ambiguous (`abab` has 2 trees, `(ab)ᵏ` has Catalan(k)).
**G3′:** `S → aBS | bAS | ε`, `A → a | bAA`, `B → b | aBB`: B derives "one more b than a, with
no balanced prefix", so every string splits uniquely.

**DPDA M3** keeps the surplus on the stack (C per unmatched credit, D per unmatched debit):

![](docs/diagrams/pda_ledger.png)

```
abba: (q0,abba,Z) ⊢ (q1,bba,CZ) ⊢ (q1,ba,Z) ⊢ (q0,ba,Z) ⊢ (q1,a,DZ) ⊢ (q1,ε,Z) ⊢ (q0,ε,Z)   accept
```

## 4. One or two per item: aⁿbⁿ ∪ aⁿb²ⁿ

**G4:** `S → S1 | S2`, `S1 → aS1b | ε`, `S2 → aS2bb | ε` is ambiguous on exactly one string, ε
(through S1 or S2). **G4′:** `S → ε | T1 | T2` with `T1 → aT1b | ab`, `T2 → aT2bb | abb`.

The PDA must decide **before reading any b** whether each a will be matched by one b or two,
so it guesses with an ε-move; this language has no DPDA. With a marker (`c` = one each, `d` =
two each) the guess disappears and a DPDA suffices.

| NPDA (guess at the start) | DPDA for aⁿ c bⁿ ∪ aⁿ d b²ⁿ |
|---|---|
| ![](docs/diagrams/npda_one_two.png) | ![](docs/diagrams/dpda_marked.png) |

## Bounded ambiguity check

`python -m pda_parsing.cli ambiguity` counts the parse trees of every short string:
G1 is ambiguous on 68 of 152 lists, G2 on 108 of 207 expressions, G3 on 320 of 351 ledgers and
G4 only on ε; every revised grammar gives one tree each and generates the same strings.
(Ambiguity is undecidable in general, so this is evidence, not a proof.)

## Tests

`tests/test_pda_parsing.py` has 28 checks, including Python's `json` and `ast` parsers as
oracles, all 8 191 strings up to length 12 for the ledger and for aⁿbⁿ ∪ aⁿb²ⁿ, all 21 845
strings up to length 7 for the marked version, and the pumping argument for every split of
[ᵖ ]ᵖ with p ≤ 8.

## Layout

```
pda_parsing/grammar.py   CFG, parse-tree counting, derivations, ambiguity check
pda_parsing/pda.py       PDA simulator, determinism check, CFG → PDA construction
pda_parsing/ll1.py       FIRST/FOLLOW, LL(1) table, predictive parser
pda_parsing/cases.py     the four case studies
pda_parsing/cli.py       terminal demo
tests/                   28 checks
tools/, docs/diagrams/   diagram generator and output
```
