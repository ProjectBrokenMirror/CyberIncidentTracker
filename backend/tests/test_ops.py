from app.models.ingestion_run import IngestionRun


def test_list_ingestion_runs_returns_recent_runs(client, db_session) -> None:
    db_session.add(
        IngestionRun(
            status="success",
            total_raw=10,
            total_normalized=10,
            total_deduped=9,
            total_persisted=8,
            total_unmatched=1,
            total_skipped_duplicates=1,
            total_organizations_created=2,
        )
    )
    db_session.commit()

    response = client.get("/api/v1/ops/ingestion-runs")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["status"] == "success"
