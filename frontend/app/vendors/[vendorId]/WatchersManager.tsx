"use client";

import { FormEvent, useState } from "react";

type VendorWatcher = {
  id: number;
  vendor_id: number;
  email: string;
  is_active: boolean;
  created_at: string;
};

export default function WatchersManager({
  vendorId,
  initialWatchers,
}: {
  vendorId: number;
  initialWatchers: VendorWatcher[];
}) {
  const [watchers, setWatchers] = useState<VendorWatcher[]>(initialWatchers);
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleAdd(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const response = await fetch(`/api/vendors/${vendorId}/watchers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, is_active: true }),
      });
      if (!response.ok) {
        setError("Failed to add watcher.");
        return;
      }
      const watcher = (await response.json()) as VendorWatcher;
      setWatchers((prev) => {
        const deduped = prev.filter((item) => item.id !== watcher.id);
        return [watcher, ...deduped];
      });
      setEmail("");
    } catch {
      setError("Failed to add watcher.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(watcherId: number) {
    setSaving(true);
    setError("");
    try {
      const response = await fetch(`/api/vendors/${vendorId}/watchers/${watcherId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        setError("Failed to remove watcher.");
        return;
      }
      const updated = (await response.json()) as VendorWatcher;
      setWatchers((prev) => prev.map((item) => (item.id === watcherId ? updated : item)));
    } catch {
      setError("Failed to remove watcher.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section style={{ marginTop: "2rem", maxWidth: "700px" }}>
      <h2>Watchlist Email Subscriptions</h2>
      <form onSubmit={handleAdd} style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
        <input
          type="email"
          placeholder="alerts@example.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
          style={{
            flex: 1,
            padding: "0.5rem",
            border: "1px solid #334155",
            background: "#0b1733",
            color: "white",
          }}
        />
        <button type="submit" disabled={saving} style={{ padding: "0.5rem 0.75rem" }}>
          Add
        </button>
      </form>
      {error ? <p style={{ color: "#fca5a5", marginTop: "0.5rem" }}>{error}</p> : null}
      {watchers.length === 0 ? (
        <p style={{ marginTop: "1rem" }}>No watcher emails configured yet.</p>
      ) : (
        <table
          style={{
            borderCollapse: "collapse",
            marginTop: "1rem",
            width: "100%",
          }}
        >
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Email</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Status</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {watchers.map((watcher) => (
              <tr key={watcher.id}>
                <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem" }}>{watcher.email}</td>
                <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem" }}>
                  {watcher.is_active ? "active" : "inactive"}
                </td>
                <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem", textAlign: "right" }}>
                  {watcher.is_active ? (
                    <button type="button" disabled={saving} onClick={() => handleDeactivate(watcher.id)}>
                      Remove
                    </button>
                  ) : (
                    <span>-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
