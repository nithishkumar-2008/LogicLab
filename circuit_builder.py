"""Turns a parsed expression (AST) into a layout-ready circuit description.

The output is plain JSON-friendly data: nodes (with x/y positions and pin
coordinates), edges (with SVG path strings) and the canvas size. The browser
only draws it; all structure and geometry decisions are made here.

Coordinates: for every node, (x, y) is the LEFT-MIDDLE point of its box.
"""
from logic_engine import BinOp, Const, Not, Var, variables

COL = 160        # horizontal distance between levels
ROW = 70         # minimum vertical distance between nodes in a level
MARGIN_X = 30
MARGIN_Y = 40
WIDTH = {"INPUT": 40, "CONST": 40, "OUTPUT": 48, "AND": 60, "OR": 60, "XOR": 60, "NOT": 46}
PIN_DX = {"OR": 7}  # OR's curved back edge: wires end slightly inside the box


def build_circuit(ast):
    nodes, by_id = [], {}

    def add(kind, label=None, inputs=()):
        node_id = f"n{len(nodes)}"
        level = 1 + max(by_id[i]["level"] for i in inputs) if inputs else 0
        node = {"id": node_id, "type": kind, "label": label, "inputs": list(inputs), "level": level}
        nodes.append(node)
        by_id[node_id] = node
        return node_id

    var_ids = {name: add("INPUT", name) for name in variables(ast)}

    def build(n):
        if isinstance(n, Var):
            return var_ids[n.name]
        if isinstance(n, Const):
            return add("CONST", str(n.value))
        if isinstance(n, Not):
            return add("NOT", None, [build(n.operand)])
        left = build(n.left)
        right = build(n.right)
        return add(n.op, None, [left, right])

    root = build(ast)
    output_id = add("OUTPUT", "OUT", [root])

    # ---- layout: one column per level, gates centred on their inputs
    levels = {}
    for node in nodes:
        levels.setdefault(node["level"], []).append(node)
    for level in sorted(levels):
        group = levels[level]
        for k, node in enumerate(group):
            node["x"] = MARGIN_X + level * COL
            if level == 0:
                node["y"] = k * ROW
            else:
                ys = [by_id[i]["y"] for i in node["inputs"]]
                node["y"] = round(sum(ys) / len(ys))
        group.sort(key=lambda n: n["y"])
        for a, b in zip(group, group[1:]):
            if b["y"] - a["y"] < ROW:
                b["y"] = a["y"] + ROW
    shift = MARGIN_Y - min(n["y"] for n in nodes)
    for node in nodes:
        node["y"] += shift

    # ---- pins
    for node in nodes:
        node["w"] = WIDTH[node["type"]]
        count = len(node["inputs"])
        ys = [node["y"] - 12, node["y"] + 12] if count == 2 else [node["y"]] if count == 1 else []
        dx = PIN_DX.get(node["type"], 0)
        node["in_pins"] = [[node["x"] + dx, y] for y in ys]
        node["out_pin"] = None if node["type"] == "OUTPUT" else [node["x"] + node["w"], node["y"]]

    # ---- wires (orthogonal paths)
    edges = []
    for node in nodes:
        for pin, src in enumerate(node["inputs"]):
            sx, sy = by_id[src]["out_pin"]
            dx, dy = node["in_pins"][pin]
            mid = dx - 20 - 6 * pin
            edges.append({"from": src, "to": node["id"], "pin": pin,
                          "path": f"M{sx},{sy} H{mid} V{dy} H{dx}"})

    return {
        "nodes": nodes,
        "edges": edges,
        "output_id": output_id,
        "width": max(n["x"] + n["w"] for n in nodes) + 90,
        "height": max(n["y"] for n in nodes) + MARGIN_Y + 30,
    }


def evaluate_circuit(circuit, inputs):
    """Compute every node's value from the circuit structure alone.

    Nodes are stored in creation order, which is already topological.
    """
    values = {}
    for node in circuit["nodes"]:
        kind = node["type"]
        args = [values[i] for i in node["inputs"]]
        if kind == "INPUT":
            value = 1 if inputs[node["label"]] else 0
        elif kind == "CONST":
            value = int(node["label"])
        elif kind == "NOT":
            value = 1 - args[0]
        elif kind == "AND":
            value = args[0] & args[1]
        elif kind == "OR":
            value = args[0] | args[1]
        elif kind == "XOR":
            value = args[0] ^ args[1]
        else:  # OUTPUT
            value = args[0]
        values[node["id"]] = value
    return values
