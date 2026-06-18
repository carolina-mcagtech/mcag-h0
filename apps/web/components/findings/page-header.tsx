"use client"

import { AlertTriangle, ArrowLeftIcon, Check, Loader2, MapPin } from "lucide-react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { type InspectionMeta } from "@/lib/findings"
import { type GlobalSaveStatus } from "@/hooks/use-findings"
import { STATUS_LABELS, type InspectionStatus } from "@/lib/inspections"
import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<InspectionStatus, string> = {
  DRAFT: "bg-slate-100 text-slate-600",
  IN_FIELD: "bg-blue-100 text-blue-700",
  PENDING_REVIEW: "bg-amber-100 text-amber-700",
  PUBLISHED: "bg-emerald-100 text-emerald-700",
  DELIVERED: "bg-violet-100 text-violet-700",
}

interface PageHeaderProps {
  inspection: InspectionMeta
  globalSaveStatus: GlobalSaveStatus
}

export function PageHeader({ inspection, globalSaveStatus }: PageHeaderProps) {
  const router = useRouter()

  return (
    <header className="border-b border-border bg-card">
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            className="-ml-1 shrink-0"
            onClick={() => router.push(`/inspections/${inspection.id}`)}
          >
            <ArrowLeftIcon data-icon="inline-start" />
            Back
          </Button>

          <div className="space-y-1.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-primary">
              Findings Entry
            </p>
            <div className="flex items-center gap-2">
              <MapPin className="size-4 text-muted-foreground" />
              <h1 className="text-base font-semibold text-foreground">
                {inspection.address}
              </h1>
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                  STATUS_STYLES[inspection.status],
                )}
              >
                {STATUS_LABELS[inspection.status]}
              </span>
            </div>
          </div>
        </div>

        {/* Auto-save status — no manual button needed */}
        <div className="flex items-center">
          {globalSaveStatus === "saving" && (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" />
              Saving…
            </span>
          )}
          {globalSaveStatus === "all-saved" && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-600">
              <Check className="size-3.5" />
              All changes saved
            </span>
          )}
          {globalSaveStatus === "error" && (
            <span className="flex items-center gap-1.5 text-xs text-amber-600">
              <AlertTriangle className="size-3.5" />
              Some changes failed to save
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
