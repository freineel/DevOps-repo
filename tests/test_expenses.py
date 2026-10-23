def _create(client, amount_cents=1250, category="Essen", spent_on="2026-10-23"):
    """Helper: POST one expense, defaults give a valid one."""
    payload = {"amount_cents": amount_cents, "category": category, "spent_on": spent_on}
    return client.post("/api/expenses", json=payload)


# --- POST /api/expenses ---------------------------------------------------


def test_create_returns_201_and_the_expense(client):
    response = _create(client)
    assert response.status_code == 201
    assert response.get_json() == {
        "id": 1,
        "amount_cents": 1250,
        "category": "Essen",
        "spent_on": "2026-10-23",
    }


def test_create_with_invalid_amount_returns_400(client):
    response = _create(client, amount_cents=0)
    assert response.status_code == 400
    assert "amount_cents" in response.get_json()["error"]


def test_create_with_invalid_date_returns_400(client):
    assert _create(client, spent_on="2026-13-45").status_code == 400


def test_create_without_body_returns_400(client):
    assert client.post("/api/expenses").status_code == 400


def test_create_with_json_list_returns_400(client):
    assert client.post("/api/expenses", json=[1, 2]).status_code == 400


# --- GET /api/expenses ----------------------------------------------------


def test_list_is_empty_at_start(client):
    response = client.get("/api/expenses")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_returns_created_expenses(client):
    _create(client)
    _create(client, category="Miete")
    assert [e["category"] for e in client.get("/api/expenses").get_json()] == ["Essen", "Miete"]


def test_list_filters_by_category(client):
    _create(client, category="Essen")
    _create(client, category="Miete")
    result = client.get("/api/expenses?category=Miete").get_json()
    assert [e["category"] for e in result] == ["Miete"]


def test_list_filters_by_month(client):
    _create(client, spent_on="2026-09-30")
    _create(client, spent_on="2026-10-01")
    result = client.get("/api/expenses?month=2026-10").get_json()
    assert [e["spent_on"] for e in result] == ["2026-10-01"]


def test_list_with_invalid_month_returns_400(client):
    assert client.get("/api/expenses?month=2026-13").status_code == 400


# --- DELETE /api/expenses/<id> --------------------------------------------


def test_delete_returns_204_and_removes_the_expense(client):
    expense_id = _create(client).get_json()["id"]
    assert client.delete(f"/api/expenses/{expense_id}").status_code == 204
    assert client.get("/api/expenses").get_json() == []


def test_delete_unknown_id_returns_404(client):
    assert client.delete("/api/expenses/999").status_code == 404


# --- GET /api/expenses/summary --------------------------------------------


def test_summary_is_zero_without_expenses(client):
    assert client.get("/api/expenses/summary").get_json() == {
        "total_cents": 0,
        "by_category": {},
        "by_month": {},
    }


def test_summary_with_mixed_categories_and_months(client):
    _create(client, amount_cents=1000, category="Essen", spent_on="2026-09-15")
    _create(client, amount_cents=250, category="Essen", spent_on="2026-10-02")
    _create(client, amount_cents=90000, category="Miete", spent_on="2026-10-01")
    assert client.get("/api/expenses/summary").get_json() == {
        "total_cents": 91250,
        "by_category": {"Essen": 1250, "Miete": 90000},
        "by_month": {"2026-09": 1000, "2026-10": 90250},
    }


def test_summary_with_single_category(client):
    _create(client, amount_cents=300)
    _create(client, amount_cents=700)
    summary = client.get("/api/expenses/summary").get_json()
    assert summary["by_category"] == {"Essen": 1000}
    assert summary["total_cents"] == 1000
