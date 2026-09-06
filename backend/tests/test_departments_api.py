import uuid


def test_list_departments_returns_15(client):
    resp = client.get("/api/v1/departments")
    assert resp.status_code == 200
    assert len(resp.json()) == 15


def test_get_department_detail(client):
    resp = client.get("/api/v1/departments/marketing")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "marketing"
    assert "weights" in body


def test_get_unknown_department_returns_404(client):
    resp = client.get("/api/v1/departments/not_a_real_dept")
    assert resp.status_code == 404


def test_similar_departments_excludes_self(client):
    resp = client.get("/api/v1/departments/technicals/similar")
    assert resp.status_code == 200
    body = resp.json()
    assert all(d["id"] != "technicals" for d in body)
    similarities = [d["similarity"] for d in body]
    assert similarities == sorted(similarities, reverse=True)


def test_similar_unknown_department_returns_404(client):
    resp = client.get(f"/api/v1/departments/{uuid.uuid4()}/similar")
    assert resp.status_code == 404


def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["departments_loaded"] == 15
    assert body["questions_loaded"] == 45
