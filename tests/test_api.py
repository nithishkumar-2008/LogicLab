import pytest

from app import EXAMPLES, app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_simulate_valid(client):
    resp = client.post("/api/simulate", json={"expression": "A AND B"})
    body = resp.get_json()
    assert resp.status_code == 200 and body["ok"]
    assert body["variables"] == ["A", "B"]
    assert body["combinations"] == 4
    assert [r["output"] for r in body["truth_table"]["rows"]] == [0, 0, 0, 1]
    assert body["circuit"]["nodes"] and body["current"]["output"] == 0


@pytest.mark.parametrize("payload", [
    {"expression": "A AND"}, {"expression": ""}, {"expression": 123}, {}, {"expression": None},
    {"expression": "A AND B AND C AND D AND E"},
])
def test_simulate_invalid_expression_is_400_with_message(client, payload):
    resp = client.post("/api/simulate", json=payload)
    body = resp.get_json()
    assert resp.status_code == 400
    assert body["ok"] is False and body["error"]["message"]
    assert "Traceback" not in resp.get_data(as_text=True)


def test_non_json_and_non_object_bodies_rejected(client):
    assert client.post("/api/simulate", data="nope", content_type="text/plain").status_code == 400
    assert client.post("/api/simulate", json=[1, 2]).status_code == 400


def test_oversized_body_rejected(client):
    resp = client.post("/api/simulate", json={"expression": "A" * 10000})
    assert resp.status_code == 413 and resp.get_json()["ok"] is False


def test_evaluate_matches_engine(client):
    resp = client.post("/api/evaluate", json={"expression": "A XOR B", "inputs": {"A": 1, "B": 0}})
    cur = resp.get_json()["current"]
    assert cur["output"] == 1 and cur["row_index"] == 2
    assert list(cur["node_values"].values())[-1] == 1


@pytest.mark.parametrize("inputs", [{"A": 2, "B": 0}, {"A": "1", "B": 0}, {"A": 1}, {"A": 1.0, "B": 0}, "x"])
def test_evaluate_rejects_bad_inputs(client, inputs):
    resp = client.post("/api/evaluate", json={"expression": "A AND B", "inputs": inputs})
    assert resp.status_code == 400


def test_unknown_api_route_is_json_404(client):
    resp = client.get("/api/nope")
    assert resp.status_code == 404 and resp.get_json()["ok"] is False


def test_examples_all_simulate(client):
    assert len(EXAMPLES) == 6
    for ex in EXAMPLES:
        assert client.post("/api/simulate", json={"expression": ex["expression"]}).status_code == 200


def test_index_page_and_security_headers(client):
    resp = client.get("/")
    assert resp.status_code == 200 and b"LogicLab" in resp.data
    assert "script-src 'self'" in resp.headers["Content-Security-Policy"]
    assert client.get("/static/js/script.js").status_code == 200
    assert client.get("/static/css/style.css").status_code == 200
