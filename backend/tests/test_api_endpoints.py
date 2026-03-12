from app.core.config import settings


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


def test_vendor_import_creates_vendors_for_orgs_with_incidents(client) -> None:
    org_a = client.post("/api/v1/organizations/", json={"canonical_name": "Vendor A"}).json()["id"]
    org_b = client.post("/api/v1/organizations/", json={"canonical_name": "Vendor B"}).json()["id"]
    org_c = client.post("/api/v1/organizations/", json={"canonical_name": "Vendor C"}).json()["id"]

    client.post(
        "/api/v1/incidents/",
        json={"org_id": org_a, "incident_type": "data_breach", "status": "new", "severity": "high", "confidence": 0.9},
    )
    client.post(
        "/api/v1/incidents/",
        json={"org_id": org_b, "incident_type": "data_breach", "status": "resolved", "severity": "medium", "confidence": 0.8},
    )

    import_response = client.post(
        "/api/v1/vendors/import",
        json={"owner": "Risk Team", "criticality": "high", "only_with_incidents": True, "limit": 50},
    )
    assert import_response.status_code == 200
    payload = import_response.json()
    assert payload["requested_count"] == 2
    assert payload["created_count"] == 2
    assert payload["skipped_existing_count"] == 0

    # Running import again should skip existing vendor rows.
    import_response_2 = client.post(
        "/api/v1/vendors/import",
        json={"owner": "Risk Team", "criticality": "high", "only_with_incidents": True, "limit": 50},
    )
    payload_2 = import_response_2.json()
    assert payload_2["requested_count"] == 2
    assert payload_2["created_count"] == 0
    assert payload_2["skipped_existing_count"] == 2

    list_vendors = client.get("/api/v1/vendors/").json()["items"]
    assert len(list_vendors) == 2
    assert all(item["organization_id"] in {org_a, org_b} for item in list_vendors)
    assert all(item["organization_id"] != org_c for item in list_vendors)


def test_vendor_incidents_endpoint_returns_timeline(client) -> None:
    org_id = client.post("/api/v1/organizations/", json={"canonical_name": "Acme"}).json()["id"]
    vendor_id = client.post("/api/v1/vendors/", json={"organization_id": org_id}).json()["id"]

    client.post(
        "/api/v1/incidents/",
        json={"org_id": org_id, "incident_type": "data_breach", "status": "new", "severity": "high", "confidence": 0.9},
    )

    response = client.get(f"/api/v1/vendors/{vendor_id}/incidents")
    assert response.status_code == 200
    payload = response.json()
    assert payload["vendor_id"] == vendor_id
    assert payload["organization_id"] == org_id
    assert len(payload["items"]) == 1
    assert payload["items"][0]["incident_type"] == "data_breach"


def test_vendor_tenant_scoping(client) -> None:
    org_id = client.post("/api/v1/organizations/", json={"canonical_name": "Tenant Scoped"}).json()["id"]
    create_response = client.post(
        "/api/v1/vendors/",
        json={"organization_id": org_id},
        headers={"X-Tenant-ID": "tenant-a"},
    )
    assert create_response.status_code == 200
    vendor_id = create_response.json()["id"]

    visible_in_tenant_a = client.get("/api/v1/vendors/", headers={"X-Tenant-ID": "tenant-a"})
    visible_in_tenant_b = client.get("/api/v1/vendors/", headers={"X-Tenant-ID": "tenant-b"})
    assert len(visible_in_tenant_a.json()["items"]) == 1
    assert len(visible_in_tenant_b.json()["items"]) == 0

    vendor_incidents_other_tenant = client.get(f"/api/v1/vendors/{vendor_id}/incidents", headers={"X-Tenant-ID": "tenant-b"})
    assert vendor_incidents_other_tenant.status_code == 404


def test_api_key_auth_toggle(client) -> None:
    previous_require = settings.require_api_key
    previous_keys = settings.api_keys
    settings.require_api_key = True
    settings.api_keys = "test-key"
    try:
        blocked = client.get("/api/v1/organizations/")
        allowed = client.get("/api/v1/organizations/", headers={"X-API-Key": "test-key"})
        assert blocked.status_code == 401
        assert allowed.status_code == 200
    finally:
        settings.require_api_key = previous_require
        settings.api_keys = previous_keys


def test_vendor_watchers_create_and_list(client) -> None:
    org_id = client.post("/api/v1/organizations/", json={"canonical_name": "Watcher Org"}).json()["id"]
    vendor_id = client.post(
        "/api/v1/vendors/",
        json={"organization_id": org_id, "owner": "Risk Team", "criticality": "high"},
        headers={"X-Tenant-ID": "tenant-a"},
    ).json()["id"]

    create = client.post(
        f"/api/v1/vendors/{vendor_id}/watchers",
        json={"email": "alerts@example.com", "is_active": True},
        headers={"X-Tenant-ID": "tenant-a"},
    )
    assert create.status_code == 200
    assert create.json()["email"] == "alerts@example.com"

    listed = client.get(f"/api/v1/vendors/{vendor_id}/watchers", headers={"X-Tenant-ID": "tenant-a"})
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    # Tenant B cannot access tenant A vendor watchers.
    denied = client.get(f"/api/v1/vendors/{vendor_id}/watchers", headers={"X-Tenant-ID": "tenant-b"})
    assert denied.status_code == 404

    deactivate = client.delete(
        f"/api/v1/vendors/{vendor_id}/watchers/{create.json()['id']}",
        headers={"X-Tenant-ID": "tenant-a"},
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False
