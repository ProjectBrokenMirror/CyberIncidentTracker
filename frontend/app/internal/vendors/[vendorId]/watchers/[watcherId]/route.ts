import { NextRequest, NextResponse } from "next/server";

import { getServerApiHeaders } from "../../../../../lib/apiHeaders";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function DELETE(_request: NextRequest, context: { params: { vendorId: string; watcherId: string } }) {
  const response = await fetch(
    `${apiBase}/api/v1/vendors/${context.params.vendorId}/watchers/${context.params.watcherId}`,
    {
      method: "DELETE",
      headers: getServerApiHeaders(),
    }
  );
  const payload = await response.text();
  return new NextResponse(payload, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
