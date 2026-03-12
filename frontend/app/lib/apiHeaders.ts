export function getServerApiHeaders(): HeadersInit {
  const headers: Record<string, string> = {};

  const apiKey = process.env.API_SERVER_KEY?.trim();
  const tenantId = process.env.API_TENANT_ID?.trim();
  const userRole = process.env.API_USER_ROLE?.trim();

  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  if (tenantId) {
    headers["X-Tenant-ID"] = tenantId;
  }
  if (userRole) {
    headers["X-User-Role"] = userRole;
  }

  return headers;
}
