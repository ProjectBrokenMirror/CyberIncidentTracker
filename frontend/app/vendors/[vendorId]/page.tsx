import Link from "next/link";
import { getServerApiHeaders } from "../../lib/apiHeaders";

type IncidentItem = {
  id: number;
  incident_type: string;
  status: string;
  severity: string;
  confidence: number;
  first_seen_at: string;
};

type VendorIncidentPayload = {
  vendor_id: number;
  organization_id: number;
  organization_name: string | null;
  items: IncidentItem[];
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function fetchVendorIncidents(vendorId: string): Promise<VendorIncidentPayload | null> {
  try {
    const response = await fetch(`${apiBase}/api/v1/vendors/${vendorId}/incidents`, {
      cache: "no-store",
      headers: getServerApiHeaders(),
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as VendorIncidentPayload;
  } catch {
    return null;
  }
}

export default async function VendorDetailPage({ params }: { params: { vendorId: string } }) {
  const payload = await fetchVendorIncidents(params.vendorId);

  return (
    <main style={{ padding: "2rem", fontFamily: "Inter, sans-serif" }}>
      <p>
        <Link href="/">Back to vendor summary</Link>
      </p>
      {!payload ? (
        <>
          <h1>Vendor not found</h1>
          <p>Check the vendor ID or create a vendor in the API first.</p>
        </>
      ) : (
        <>
          <h1>{payload.organization_name ?? "Vendor"}</h1>
          <p>
            Vendor #{payload.vendor_id} | Organization #{payload.organization_id}
          </p>
          <h2 style={{ marginTop: "1.5rem" }}>Incident Timeline</h2>
          {payload.items.length === 0 ? (
            <p>No incidents found for this vendor's organization.</p>
          ) : (
            <table
              style={{
                borderCollapse: "collapse",
                marginTop: "1rem",
                width: "100%",
                maxWidth: "1000px",
              }}
            >
              <thead>
                <tr>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Date</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Type</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Status</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #334155", padding: "0.5rem" }}>Severity</th>
                  <th style={{ textAlign: "right", borderBottom: "1px solid #334155", padding: "0.5rem" }}>
                    Confidence
                  </th>
                </tr>
              </thead>
              <tbody>
                {payload.items.map((item) => (
                  <tr key={item.id}>
                    <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem" }}>
                      {new Date(item.first_seen_at).toLocaleString()}
                    </td>
                    <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem" }}>{item.incident_type}</td>
                    <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem" }}>{item.status}</td>
                    <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem" }}>{item.severity}</td>
                    <td style={{ borderBottom: "1px solid #1e293b", padding: "0.5rem", textAlign: "right" }}>
                      {(item.confidence * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </main>
  );
}
