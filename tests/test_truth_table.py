import pytest

from logic_engine import evaluate, parse_expression, truth_table, variables


def table(expr):
    return truth_table(parse_expression(expr))


def outputs(expr):
    return "".join(str(r["output"]) for r in table(expr))


@pytest.mark.parametrize("expr,expected", [
    ("A AND B", "0001"),
    ("A OR B", "0111"),
    ("NOT A", "10"),
    ("A XOR B", "0110"),
    ("(A AND B) OR (B AND C) OR (A AND C)", "00010111"),
    ("(A OR B) AND (NOT C XOR D)", "0000100110011001"),
    ("(A AND B) OR NOT C", "10101011"),
])
def test_documented_examples(expr, expected):
    assert outputs(expr) == expected


@pytest.mark.parametrize("expr,n", [
    ("1", 0), ("A", 1), ("A AND B", 2), ("A OR B OR C", 3), ("A AND B AND C AND D", 4),
])
def test_row_count_is_two_to_the_n(expr, n):
    assert len(table(expr)) == 2 ** n


def test_binary_counting_order_first_variable_is_msb():
    assert [r["inputs"] for r in table("A OR B")] == [[0, 0], [0, 1], [1, 0], [1, 1]]


def test_rows_are_unique_and_complete():
    rows = [tuple(r["inputs"]) for r in table("A XOR B XOR C XOR D")]
    assert len(set(rows)) == 16


def test_constant_expression_has_one_row():
    assert table("1") == [{"inputs": [], "output": 1}]
    assert table("0 OR 0") == [{"inputs": [], "output": 0}]


def test_tautology_and_contradiction():
    assert set(outputs("A OR NOT A")) == {"1"}
    assert set(outputs("A AND NOT A")) == {"0"}


def test_majority_matches_independent_python_logic():
    for r in table("(A AND B) OR (B AND C) OR (A AND C)"):
        assert r["output"] == (1 if sum(r["inputs"]) >= 2 else 0)


def test_nested_matches_independent_python_logic():
    ast = parse_expression("(A OR B) AND (NOT C XOR D)")
    names = variables(ast)
    for row in truth_table(ast):
        a, b, c, d = row["inputs"]
        expected = int((a or b) and ((not c) != bool(d)))
        assert evaluate(ast, dict(zip(names, row["inputs"]))) == expected == row["output"]


def test_de_morgan():
    assert outputs("NOT (A AND B)") == outputs("NOT A OR NOT B")
    assert outputs("NOT (A OR B)") == outputs("NOT A AND NOT B")
