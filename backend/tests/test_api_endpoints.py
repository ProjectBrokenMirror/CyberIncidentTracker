def test_create_and_list_organizations(client) -> None:
    create_response = client.post(
        "/api/v1/organizations/",
        json={"canonical_name": "Acme Corp", "domain": "acme.example"},
    )
    assert create_response.status_code == 200
    assert create_response.json()["canonical_name"] == "Acme Corp"

    list_response = client.get("/api/v1/organizations/")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload["items"]) == 1


def test_create_and_get_incident(client) -> None:
    org_response = client.post(
        "/api/v1/organizations/",
        json={"canonical_name": "Globex", "domain": "globex.example"},
    )
    org_id = org_response.json()["id"]

    incident_response = client.post(
        "/api/v1/incidents/",
        json={
            "org_id": org_id,
            "incident_type": "data_breach",
            "status": "new",
            "severity": "high",
            "confidence": 0.8,
        },
    )
    assert incident_response.status_code == 200
    incident_id = incident_response.json()["id"]

    fetch_response = client.get(f"/api/v1/incidents/{incident_id}")
    assert fetch_response.status_code == 200
    assert fetch_response.json()["org_id"] == org_id
