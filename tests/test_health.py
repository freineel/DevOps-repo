def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_health_reports_version(client):
    assert client.get("/health").get_json()["version"] == "test"


def test_ready_reports_ready_with_in_memory_repository(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"


def test_ready_returns_503_when_repository_is_unhealthy(app, client):
    class BrokenRepository:
        def healthy(self):
            return False

    app.extensions["repository"] = BrokenRepository()
    assert client.get("/ready").status_code == 503


def test_metrics_endpoint_is_exposed(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"expense_tracker_info" in response.data


def test_metrics_use_route_template_not_real_path(client):
    # Two deletes with different ids must end up in ONE time series,
    # otherwise every id would create a new series in Prometheus.
    created = client.post(
        "/api/expenses",
        json={"amount_cents": 500, "category": "food", "spent_on": "2026-11-24"},
    )
    expense_id = created.get_json()["id"]
    client.delete(f"/api/expenses/{expense_id}")
    client.delete("/api/expenses/999999")
    client.get("/does-not-exist")

    body = client.get("/metrics").get_data(as_text=True)
    assert 'url_rule="/api/expenses/<int:expense_id>"' in body
    assert 'url_rule="None"' in body
    assert f"/api/expenses/{expense_id}" not in body
    assert "/does-not-exist" not in body
