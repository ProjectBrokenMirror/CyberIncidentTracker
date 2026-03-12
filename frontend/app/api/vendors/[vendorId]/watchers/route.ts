import { NextRequest, NextResponse } from "next/server";

import { getServerApiHeaders } from "../../../../lib/apiHeaders";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function GET(_request: NextRequest, context: { params: { vendorId: string } }) {
  const response = await fetch(`${apiBase}/api/v1/vendors/${context.params.vendorId}/watchers`, {
    cache: "no-store",
    headers: getServerApiHeaders(),
  });
  const payload = await response.text();
  return new NextResponse(payload, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function POST(request: NextRequest, context: { params: { vendorId: string } }) {
  const body = await request.text();
  const response = await fetch(`${apiBase}/api/v1/vendors/${context.params.vendorId}/watchers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getServerApiHeaders(),
    },
    body,
  });
  const payload = await response.text();
  return new NextResponse(payload, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
