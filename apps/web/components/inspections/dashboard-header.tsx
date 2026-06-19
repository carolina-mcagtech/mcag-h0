"use client"

import { ShieldCheck, ChevronDown, User, Settings, LogOut } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { type TenantResponse, getEffectiveBrandName } from "@/lib/tenant"

export function DashboardHeader({ tenant }: { tenant: TenantResponse | null }) {
  const inspectorName = tenant?.theme_config.inspector_name ?? "Inspector"
  const initials = (tenant?.theme_config.inspector_name ?? "IN")
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0].toUpperCase())
    .slice(0, 2)
    .join("")
  const brandName = tenant ? getEffectiveBrandName(tenant) : "InspectIQ"
  const logoUrl = tenant?.theme_config.logo_url ?? null

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-card/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-full items-center justify-between px-4 sm:px-6">
        <div className="flex min-w-0 flex-1 overflow-hidden items-center gap-2 mr-4">
          <>
            {logoUrl && (
              <img
                src={logoUrl}
                alt={brandName}
                className="max-h-8 max-w-40 object-contain"
                onError={(e) => { e.currentTarget.style.display = "none" }}
              />
            )}
            {!logoUrl && (
              <div className="flex shrink-0 size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <ShieldCheck className="size-5" aria-hidden="true" />
              </div>
            )}
            <span className="min-w-0 truncate text-lg font-semibold tracking-tight text-foreground">
              {brandName}
            </span>
          </>
        </div>

        <div className="shrink-0">
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <Avatar className="size-8">
                <AvatarFallback className="bg-secondary text-xs font-medium text-secondary-foreground">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <span className="hidden font-medium text-foreground sm:inline">
                {inspectorName}
              </span>
              <ChevronDown
                className="size-4 text-muted-foreground"
                aria-hidden="true"
              />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuLabel className="flex flex-col gap-0.5">
                <span>{inspectorName}</span>
                {tenant?.theme_config.license_number && (
                  <span className="text-xs font-normal text-muted-foreground">
                    FL License #{tenant.theme_config.license_number}
                  </span>
                )}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="size-4" aria-hidden="true" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem render={<a href="/settings" />}>
                <Settings className="size-4" aria-hidden="true" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <LogOut className="size-4" aria-hidden="true" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
