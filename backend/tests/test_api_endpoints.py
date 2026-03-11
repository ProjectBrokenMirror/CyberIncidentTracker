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


def test_vendor_summary_returns_incident_counts(client) -> None:
    org_response = client.post(
        "/api/v1/organizations/",
        json={"canonical_name": "Blue Bird Corp", "domain": "bluebird.example"},
    )
    org_id = org_response.json()["id"]

    vendor_response = client.post(
        "/api/v1/vendors/",
        json={"organization_id": org_id, "owner": "Risk Team", "criticality": "high"},
    )
    assert vendor_response.status_code == 200

    client.post(
        "/api/v1/incidents/",
        json={
            "org_id": org_id,
            "incident_type": "data_breach",
            "status": "new",
            "severity": "high",
            "confidence": 0.9,
        },
    )
    client.post(
        "/api/v1/incidents/",
        json={
            "org_id": org_id,
            "incident_type": "service_disruption",
            "status": "resolved",
            "severity": "medium",
            "confidence": 0.7,
        },
    )

    summary_response = client.get("/api/v1/vendors/summary")
    assert summary_response.status_code == 200
    items = summary_response.json()["items"]
    assert len(items) == 1
    assert items[0]["organization_name"] == "Blue Bird Corp"
    assert items[0]["total_incidents"] == 2
    assert items[0]["new_incidents"] == 1
    assert items[0]["resolved_incidents"] == 1
