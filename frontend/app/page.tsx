import Link from "next/link";

type VendorSummary = {
  vendor_id: number;
  organization_id: number;
  organization_name: string;
  criticality: string;
  total_incidents: number;
  new_incidents: number;
  resolved_incidents: number;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function fetchVendorSummary(): Promise<VendorSummary[]> {
  try {
    const response = await fetch(`${apiBase}/api/v1/vendors/summary`, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }
    const payload = (await response.json()) as { items?: VendorSummary[] };
    return payload.items ?? [];
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const vendors = await fetchVendorSummary();

  return (
    <main style={{ padding: "2rem", fontFamily: "Inter, sans-serif" }}>
      <h1>Cyber Incident Tracker</h1>
      <p>Know before it matters.</p>
      <p>Vendor risk monitoring MVP scaffold is ready.</p>

      <h2 style={{ marginTop: "2rem" }}>Vendor Portfolio Summary</h2>
      {vendors.length === 0 ? (
        <p>No vendor summary data available yet.</p>
      ) : (
        <table
          style={{
            borderCollapse: "collapse",
            marginTop: "1rem",
            width: "100%",
            maxWidth: "900px",
          }}
        >
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Organization</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Criticality</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Total</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #334155", padding: "0.5rem" }}>New</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Resolved</th>
            </tr>
          </thead>
          <tbody>
            {vendors.map((vendor) => (
              <tr key={vendor.vendor_id}>
                <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem" }}>
                  <Link href={`/vendors/${vendor.vendor_id}`}>{vendor.organization_name}</Link>
                </td>
                <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem", textTransform: "capitalize" }}>
                  {vendor.criticality}
                </td>
                <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem", textAlign: "right" }}>
                  {vendor.total_incidents}
                </td>
                <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem", textAlign: "right" }}>
                  {vendor.new_incidents}
                </td>
                <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem", textAlign: "right" }}>
                  {vendor.resolved_incidents}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
