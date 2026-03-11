def deduplicate(records: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict] = []
    for record in records:
        key = (record.get("source_name", ""), record.get("title", ""), record.get("source_url", ""))
        if key in seen:
            continue
        seen.add(key)
        output.append(record)
    return output
