// apps/web/lib/tenant.ts

export interface ThemeConfig {
  primary_color: string | null
  logo_url: string | null
  brand_name: string | null
}

export interface TenantResponse {
  id: string
  name: string
  subdomain: string
  theme_config: ThemeConfig
  plan: string
  is_active: boolean
}

export function getEffectiveBrandName(tenant: TenantResponse): string {
  return tenant.theme_config.brand_name ?? tenant.name ?? "InspectIQ"
}
