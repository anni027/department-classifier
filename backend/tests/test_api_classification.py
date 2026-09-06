import uuid


def _start(client):
    resp = client.post("/api/v1/classification/start")
    assert resp.status_code == 201
    return resp.json()


def test_start_returns_seed_question_q01(client):
    body = _start(client)
    assert body["question"]["id"] == "q01"
    assert body["question_number"] == 1
    assert body["total_max_questions"] == 12
    uuid.UUID(body["session_id"])  # valid UUID


def test_answer_unknown_session_returns_404(client):
    resp = client.post(
        "/api/v1/classification/answer",
        json={"session_id": str(uuid.uuid4()), "question_id": "q01", "response": 3},
    )
    assert resp.status_code == 404


def test_answer_wrong_question_id_returns_400(client):
    start = _start(client)
    resp = client.post(
        "/api/v1/classification/answer",
        json={"session_id": start["session_id"], "question_id": "q99", "response": 3},
    )
    assert resp.status_code == 400


def test_answer_duplicate_returns_400(client):
    start = _start(client)
    session_id = start["session_id"]
    first = client.post(
        "/api/v1/classification/answer",
        json={"session_id": session_id, "question_id": "q01", "response": 3},
    )
    assert first.status_code == 200
    duplicate = client.post(
        "/api/v1/classification/answer",
        json={"session_id": session_id, "question_id": "q01", "response": 3},
    )
    assert duplicate.status_code == 400


def test_answer_response_out_of_range_returns_422(client):
    start = _start(client)
    resp = client.post(
        "/api/v1/classification/answer",
        json={"session_id": start["session_id"], "question_id": "q01", "response": 6},
    )
    assert resp.status_code == 422


def test_full_flow_reaches_completed_result(client):
    start = _start(client)
    session_id = start["session_id"]
    question_id = start["question"]["id"]

    for _ in range(30):  # generous upper bound; real cap is 12
        resp = client.post(
            "/api/v1/classification/answer",
            json={"session_id": session_id, "question_id": question_id, "response": 4},
        )
        assert resp.status_code == 200
        body = resp.json()
        if body["completed"]:
            result = body["result"]
            assert 0.0 <= result["recommended_department"]["probability"] <= 1.0
            assert result["recommended_department"]["id"] != result["runner_up"]["id"]
            assert len(result["top_traits"]) == 3
            assert len(result["explanation"]["what_youll_do"]) > 0

            top_matches = result["top_matches"]
            assert len(top_matches) == 3
            assert top_matches[0]["id"] == result["recommended_department"]["id"]
            assert top_matches[1]["id"] == result["runner_up"]["id"]
            probs = [m["probability"] for m in top_matches]
            assert probs == sorted(probs, reverse=True)
            break
        question_id = body["question"]["id"]
    else:
        raise AssertionError("session never completed within 30 answers")


def test_answer_after_completed_returns_409(client):
    start = _start(client)
    session_id = start["session_id"]
    question_id = start["question"]["id"]

    completed = False
    for _ in range(30):
        resp = client.post(
            "/api/v1/classification/answer",
            json={"session_id": session_id, "question_id": question_id, "response": 4},
        )
        body = resp.json()
        if body["completed"]:
            completed = True
            break
        question_id = body["question"]["id"]
    assert completed

    resp = client.post(
        "/api/v1/classification/answer",
        json={"session_id": session_id, "question_id": question_id, "response": 3},
    )
    assert resp.status_code == 409


def test_status_endpoint_tracks_progress(client):
    start = _start(client)
    session_id = start["session_id"]

    status = client.get(f"/api/v1/classification/status/{session_id}").json()
    assert status["questions_answered"] == 0
    assert status["completed"] is False

    client.post(
        "/api/v1/classification/answer",
        json={"session_id": session_id, "question_id": start["question"]["id"], "response": 4},
    )
    status = client.get(f"/api/v1/classification/status/{session_id}").json()
    assert status["questions_answered"] == 1


def test_status_unknown_session_returns_404(client):
    resp = client.get(f"/api/v1/classification/status/{uuid.uuid4()}")
    assert resp.status_code == 404
