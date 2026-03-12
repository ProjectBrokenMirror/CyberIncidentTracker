import { NextRequest } from "next/server";

import { getServerApiHeaders } from "../../../../lib/apiHeaders";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function GET(_request: NextRequest, context: { params: { vendorId: string } }) {
  const response = await fetch(`${apiBase}/api/v1/vendors/${context.params.vendorId}/alerts.csv`, {
    cache: "no-store",
    headers: getServerApiHeaders(),
  });
  const payload = await response.text();
  const contentDisposition =
    response.headers.get("content-disposition") ?? `attachment; filename="vendor-${context.params.vendorId}-alerts.csv"`;
  return new Response(payload, {
    status: response.status,
    headers: {
      "Content-Type": "text/csv",
      "Content-Disposition": contentDisposition,
    },
  });
}
