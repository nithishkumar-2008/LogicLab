import pytest

from logic_engine import (LogicError, MAX_EXPRESSION_LENGTH, evaluate, parse_expression,
                          to_string, variables)


def ev(expr, **values):
    return evaluate(parse_expression(expr), values)


@pytest.mark.parametrize("a,b,expected", [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)])
def test_and(a, b, expected):
    assert ev("A AND B", A=a, B=b) == expected


@pytest.mark.parametrize("a,b,expected", [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1)])
def test_or(a, b, expected):
    assert ev("A OR B", A=a, B=b) == expected


@pytest.mark.parametrize("a,expected", [(0, 1), (1, 0)])
def test_not(a, expected):
    assert ev("NOT A", A=a) == expected


@pytest.mark.parametrize("a,b,expected", [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)])
def test_xor(a, b, expected):
    assert ev("A XOR B", A=a, B=b) == expected


def test_symbols_match_keywords():
    for sym, word in [("A ∧ B", "A AND B"), ("A ∨ B", "A OR B"),
                      ("A ⊕ B", "A XOR B"), ("¬A", "NOT A")]:
        assert parse_expression(sym) == parse_expression(word)


def test_case_insensitive():
    assert parse_expression("a and not b") == parse_expression("A AND NOT B")


def test_precedence_and_over_or():
    # A OR (B AND C) = 1, but (A OR B) AND C = 0
    assert ev("A OR B AND C", A=1, B=0, C=0) == 1


def test_precedence_xor_over_or():
    # (A XOR B) OR C = 1, but A XOR (B OR C) = 0
    assert ev("A XOR B OR C", A=1, B=1, C=1) == 1


def test_precedence_and_over_xor():
    # (A AND B) XOR C = 1, but A AND (B XOR C) = 0
    assert ev("A AND B XOR C", A=0, B=1, C=1) == 1


def test_precedence_not_binds_tightest():
    # (NOT A) AND B = 0, but NOT (A AND B) = 1
    assert ev("NOT A AND B", A=0, B=0) == 0


def test_parentheses_override_precedence():
    assert ev("NOT (A AND B)", A=0, B=0) == 1
    assert ev("(A OR B) AND C", A=1, B=0, C=0) == 0


def test_double_negation():
    assert ev("NOT NOT A", A=1) == 1


def test_variables_sorted_and_unique():
    assert variables(parse_expression("D OR A AND D OR B")) == ["A", "B", "D"]


def test_constants():
    assert ev("1 AND A", A=1) == 1
    assert ev("0 OR A", A=0) == 0


def test_round_trip_through_to_string():
    for expr in ["A AND B AND C", "A AND (B AND C)", "NOT (A OR B) XOR C", "NOT NOT A"]:
        ast = parse_expression(expr)
        assert parse_expression(to_string(ast)) == ast


@pytest.mark.parametrize("bad", [
    "", "   ", "A AND", "AND A", "A B", "(A AND B", "A AND B)", "()", "A AND AND B",
    "A $ B", "foo AND A", "NOT", "A NOT B", "A AND ()", "__import__('os')", "A OR OR",
    "( A B )", "10",
])
def test_invalid_expressions_raise_logic_error(bad):
    with pytest.raises(LogicError) as info:
        parse_expression(bad)
    assert info.value.message


def test_non_string_rejected():
    with pytest.raises(LogicError):
        parse_expression(None)


def test_too_long_rejected():
    with pytest.raises(LogicError):
        parse_expression("A AND " * 100 + "B")
    assert len("A AND " * 100) > MAX_EXPRESSION_LENGTH


def test_too_deep_rejected_without_recursion_error():
    with pytest.raises(LogicError):
        parse_expression("(" * 60 + "A" + ")" * 60)
    with pytest.raises(LogicError):
        parse_expression("NOT " * 60 + "A")


def test_too_many_variables_rejected():
    parse_expression("A AND B AND C AND D")
    with pytest.raises(LogicError):
        parse_expression("A AND B AND C AND D AND E")


def test_missing_variable_value_is_an_error():
    with pytest.raises(LogicError):
        evaluate(parse_expression("A AND B"), {"A": 1})


def test_error_positions_point_into_the_text():
    with pytest.raises(LogicError) as info:
        parse_expression("A AND $")
    assert info.value.position == 6
