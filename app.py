"""LogicLab Flask app: routes and request validation only.

All Boolean logic lives in logic_engine.py, all circuit geometry in circuit_builder.py.
"""
import logging
import os

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from circuit_builder import build_circuit, evaluate_circuit
from logic_engine import (LogicError, evaluate, explain, operators_used, parse_expression,
                          row_index, to_string, truth_table, variables)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024  # requests are tiny; reject anything bigger
log = logging.getLogger("logiclab")

EXAMPLES = [
    {"name": "Basic AND gate", "expression": "A AND B"},
    {"name": "Basic OR gate", "expression": "A OR B"},
    {"name": "NOT gate", "expression": "NOT A"},
    {"name": "XOR gate", "expression": "A XOR B"},
    {"name": "Majority function (3 inputs)", "expression": "(A AND B) OR (B AND C) OR (A AND C)"},
    {"name": "Nested expression", "expression": "(A OR B) AND (NOT C XOR D)"},
]


class ApiError(Exception):
    def __init__(self, message, status=400, position=None):
        super().__init__(message)
        self.message, self.status, self.position = message, status, position


def error_response(message, status, position=None):
    return jsonify({"ok": False, "error": {"message": message, "position": position}}), status


@app.errorhandler(ApiError)
def handle_api_error(e):
    return error_response(e.message, e.status, e.position)


@app.errorhandler(HTTPException)
def handle_http_error(e):
    if request.path.startswith("/api/"):
        return error_response(e.description or e.name, e.code)
    return e


@app.errorhandler(Exception)
def handle_unexpected(e):
    log.exception("Unexpected error")  # details stay in the server log only
    return error_response("Something went wrong on the server.", 500)


@app.after_request
def security_headers(resp):
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:")
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


def read_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body must be a JSON object.")
    return data


def parse_from_body(data):
    expression = data.get("expression")
    if not isinstance(expression, str):
        raise ApiError("'expression' must be a string.")
    try:
        return expression.strip(), parse_expression(expression)
    except LogicError as e:
        raise ApiError(e.message, 400, e.position)


def read_inputs(raw, names):
    """Validate {"A": 0/1, ...}. None means 'all zeros'."""
    if raw is None:
        return {n: 0 for n in names}
    if not isinstance(raw, dict):
        raise ApiError("'inputs' must be an object like {\"A\": 1}.")
    values = {}
    for n in names:
        v = raw.get(n)
        if type(v) not in (int, bool) or v not in (0, 1):
            raise ApiError(f"Input {n} must be 0 or 1.")
        values[n] = int(v)
    return values


def current_state(ast, circuit, names, values):
    output = evaluate(ast, values)
    state = {"inputs": values, "output": output, "row_index": row_index([values[n] for n in names])}
    if circuit is not None:
        node_values = evaluate_circuit(circuit, values)
        if node_values[circuit["output_id"]] != output:  # engine and circuit must never disagree
            raise RuntimeError("Circuit output does not match expression evaluator")
        state["node_values"] = node_values
    return state


def try_circuit(ast):
    try:
        return build_circuit(ast), None
    except Exception:
        log.exception("Circuit build failed")
        return None, "The circuit diagram could not be generated for this expression."


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/examples")
def examples():
    return jsonify({"ok": True, "examples": EXAMPLES})


@app.post("/api/simulate")
def simulate():
    data = read_json_body()
    text, ast = parse_from_body(data)
    names = variables(ast)
    values = read_inputs(data.get("inputs"), names)
    circuit, circuit_error = try_circuit(ast)
    return jsonify({
        "ok": True,
        "expression": text,
        "normalized": to_string(ast),
        "variables": names,
        "operators": operators_used(ast),
        "combinations": 2 ** len(names),
        "truth_table": {"variables": names, "rows": truth_table(ast)},
        "circuit": circuit,
        "circuit_error": circuit_error,
        "explanation": explain(ast),
        "current": current_state(ast, circuit, names, values),
    })


@app.post("/api/evaluate")
def evaluate_inputs():
    data = read_json_body()
    _, ast = parse_from_body(data)
    names = variables(ast)
    values = read_inputs(data.get("inputs", {}), names)
    circuit, _ = try_circuit(ast)
    return jsonify({"ok": True, "current": current_state(ast, circuit, names, values)})


if __name__ == "__main__":
    # Debug mode is OFF unless you explicitly set LOGICLAB_DEBUG=1 for local development.
    app.run(host="127.0.0.1", port=5000, debug=os.environ.get("LOGICLAB_DEBUG") == "1")
