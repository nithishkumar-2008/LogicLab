import pytest

from app import EXAMPLES
from circuit_builder import ROW, build_circuit, evaluate_circuit
from logic_engine import evaluate, parse_expression, truth_table, variables


def circuit_for(expr):
    return build_circuit(parse_expression(expr))


def types(circuit):
    return [n["type"] for n in circuit["nodes"]]


def by_id(circuit):
    return {n["id"]: n for n in circuit["nodes"]}


def test_simple_and_structure():
    assert types(circuit_for("A AND B")) == ["INPUT", "INPUT", "AND", "OUTPUT"]


def test_gate_counts_match_operators():
    t = types(circuit_for("(A OR B) AND (NOT C XOR D)"))
    assert (t.count("OR"), t.count("AND"), t.count("XOR"), t.count("NOT")) == (1, 1, 1, 1)
    assert t.count("INPUT") == 4


def test_parentheses_change_circuit_structure():
    c1 = circuit_for("A AND (B OR C)")
    n1 = by_id(c1)
    root1 = n1[c1["nodes"][-1]["inputs"][0]]
    assert root1["type"] == "AND"
    assert [n1[i]["type"] for i in root1["inputs"]] == ["INPUT", "OR"]

    c2 = circuit_for("(A AND B) OR C")
    n2 = by_id(c2)
    root2 = n2[c2["nodes"][-1]["inputs"][0]]
    assert root2["type"] == "OR"
    assert [n2[i]["type"] for i in root2["inputs"]] == ["AND", "INPUT"]


def test_each_variable_has_exactly_one_input_node():
    c = circuit_for("(A AND B) OR (B AND A) OR NOT A")
    labels = [n["label"] for n in c["nodes"] if n["type"] == "INPUT"]
    assert sorted(labels) == ["A", "B"]


def test_edges_match_node_inputs_and_flow_left_to_right():
    c = circuit_for("(A OR B) AND (NOT C XOR D)")
    nodes = by_id(c)
    assert len(c["edges"]) == sum(len(n["inputs"]) for n in c["nodes"])
    for e in c["edges"]:
        assert nodes[e["from"]]["x"] < nodes[e["to"]]["x"]


def test_nodes_in_same_column_do_not_overlap():
    c = circuit_for("(A AND B) OR (B AND C) OR (A AND C)")
    columns = {}
    for n in c["nodes"]:
        columns.setdefault(n["x"], []).append(n["y"])
    for ys in columns.values():
        ys.sort()
        assert all(b - a >= ROW for a, b in zip(ys, ys[1:]))


def test_constants_get_a_node():
    assert "CONST" in types(circuit_for("A AND 1"))


@pytest.mark.parametrize("expr", [e["expression"] for e in EXAMPLES] + [
    "1", "0 OR A", "NOT NOT A", "A XOR B XOR C XOR D", "NOT (A AND B) OR (C XOR 1)",
])
def test_circuit_output_matches_evaluator_for_every_row(expr):
    ast = parse_expression(expr)
    circuit = build_circuit(ast)
    names = variables(ast)
    for row in truth_table(ast):
        values = dict(zip(names, row["inputs"]))
        node_values = evaluate_circuit(circuit, values)
        assert node_values[circuit["output_id"]] == row["output"] == evaluate(ast, values)
