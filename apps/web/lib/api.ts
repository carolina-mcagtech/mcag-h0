// apps/web/lib/api.ts
export const DEV_TENANT_ID = '00000000-0000-0000-0000-000000000001'

export const tenantHeaders: HeadersInit = {
  'X-Tenant-ID': DEV_TENANT_ID,
}
