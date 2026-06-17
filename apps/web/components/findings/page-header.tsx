"use client"

import { AlertTriangle, Check, Loader2, MapPin, Save } from "lucide-react"
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
  onFlush: () => void
}

export function PageHeader({ inspection, globalSaveStatus, onFlush }: PageHeaderProps) {
  const isBusy = globalSaveStatus === "saving"
  const isAllSaved = globalSaveStatus === "all-saved"

  return (
    <header className="border-b border-border bg-card">
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4">
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

        <div className="flex items-center gap-3">
          {/* Global status indicator */}
          {globalSaveStatus === "saving" && (
            <span className="hidden items-center gap-1.5 text-xs text-muted-foreground sm:inline-flex">
              <Loader2 className="size-3.5 animate-spin" />
              Saving…
            </span>
          )}
          {globalSaveStatus === "all-saved" && (
            <span className="hidden items-center gap-1.5 text-xs text-emerald-600 sm:inline-flex">
              <Check className="size-3.5" />
              All changes saved
            </span>
          )}
          {globalSaveStatus === "error" && (
            <span className="hidden items-center gap-1.5 text-xs text-amber-600 sm:inline-flex">
              <AlertTriangle className="size-3.5" />
              Some changes failed to save
            </span>
          )}

          {/* Save all button — flushes debounced / draft / error rows immediately */}
          <Button
            type="button"
            onClick={onFlush}
            disabled={isBusy || isAllSaved}
            variant={globalSaveStatus === "error" ? "outline" : "default"}
          >
            <Save />
            {isAllSaved ? "All saved" : "Save all"}
          </Button>
        </div>
      </div>
    </header>
  )
}
