"""Rebuild docs/diagrams (PDA state diagrams and parse trees). Needs Graphviz (`dot`)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pda_parsing.cases import (G1, G1_REVISED, G2, G2_REVISED, G3, G3_REVISED,  # noqa: E402
                               LEDGER_DPDA, LIST_DPDA, ONE_TWO_DPDA, ONE_TWO_NPDA)
from pda_parsing.grammar import tree_to_dot  # noqa: E402

OUT = ROOT / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def save(name, dot):
    (OUT / f"{name}.dot").write_text(dot, encoding="utf-8")
    subprocess.run(["dot", "-Tsvg", "-o", str(OUT / f"{name}.svg")], input=dot.encode(), check=True)
    subprocess.run(["dot", "-Gdpi=170", "-Tpng", "-o", str(OUT / f"{name}.png")],
                   input=dot.encode(), check=True)
    print("wrote", name)


save("pda_lists", LIST_DPDA.to_dot())
save("pda_ledger", LEDGER_DPDA.to_dot(labels={
    ("q0", "q1"): ["a, Z / CZ", "b, Z / DZ"],
    ("q1", "q1"): ["a, C / CC", "a, D / ε", "b, D / DD", "b, C / ε"],
    ("q1", "q0"): ["ε, Z / Z"]}))
save("npda_one_two", ONE_TWO_NPDA.to_dot(labels={
    ("s", "p1"): ["ε, Z / Z  (guess: one b each)"],
    ("s", "p2"): ["ε, Z / Z  (guess: two b each)"],
    ("p1", "p1"): ["a, Y / XY"], ("p2", "p2"): ["a, Y / XXY"],
    ("p1", "r"): ["b, X / ε"], ("p2", "r"): ["b, X / ε"],
    ("r", "r"): ["b, X / ε"], ("p1", "f"): ["ε, Z / Z"], ("p2", "f"): ["ε, Z / Z"],
    ("r", "f"): ["ε, Z / Z"]}))
save("dpda_marked", ONE_TWO_DPDA.to_dot(labels={
    ("p", "p"): ["a, Y / XY"], ("p", "one"): ["c, Y / Y"], ("p", "two"): ["d, Y / Y"],
    ("one", "one"): ["b, X / ε"], ("two", "half"): ["b, X / X"], ("half", "two"): ["b, X / ε"],
    ("one", "f"): ["ε, Z / Z"], ("two", "f"): ["ε, Z / Z"]}))

for k, t in enumerate(G1.trees(list("[x,x,x]")), 1):
    save(f"tree_list_ambiguous_{k}", tree_to_dot(t, f"G1, tree {k} of [x,x,x]"))
save("tree_list_revised", tree_to_dot(G1_REVISED.trees(list("[x,x,x]"))[0], "G1′ (only tree)"))
w = G2.tokenize("p or p and p")
for t in G2.trees(w):
    top = "or" if t[1][1][0] == "or" else "and"
    save(f"tree_bool_{top}_root", tree_to_dot(t, f"'{top}' at the root"))
save("tree_bool_revised", tree_to_dot(G2_REVISED.trees(w)[0], "G2′ (only tree)"))
for k, t in enumerate(G3.trees(list("abab")), 1):
    save(f"tree_ledger_ambiguous_{k}", tree_to_dot(t, f"G3, tree {k} of abab"))
save("tree_ledger_revised", tree_to_dot(G3_REVISED.trees(list("abab"))[0], "G3′ (only tree)"))
