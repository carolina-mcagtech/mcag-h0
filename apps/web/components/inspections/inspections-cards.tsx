"use client"

import { useRouter } from "next/navigation"
import { ChevronRight, Trash2 } from "lucide-react"
import {
  formatFee,
  formatScheduledAt,
  type Inspection,
} from "@/lib/inspections"
import { StatusBadge } from "./status-badge"
import { InspectionTypePills } from "./inspection-type-pills"

export function InspectionsCards({
  inspections,
  onDelete,
}: {
  inspections: Inspection[]
  onDelete?: (id: string) => void
}) {
  const router = useRouter()

  return (
    <div className="flex flex-col gap-3 md:hidden">
      {inspections.map((inspection) => (
        <div
          key={inspection.id}
          className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/50"
        >
          <div className="flex items-start justify-between gap-3">
            <button
              type="button"
              onClick={() => router.push(`/inspections/${inspection.id}`)}
              aria-label={`View inspection at ${inspection.property_address}`}
              className="flex min-w-0 flex-1 items-start gap-2 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
            >
              <span className="font-semibold leading-snug text-foreground">
                {inspection.property_address}
              </span>
              <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
            </button>
            {onDelete && (
              <button
                type="button"
                aria-label={`Delete inspection at ${inspection.property_address}`}
                onClick={() => onDelete(inspection.id)}
                className="inline-flex size-7 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-destructive/10 hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Trash2 className="size-3.5" />
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={() => router.push(`/inspections/${inspection.id}`)}
            className="flex flex-col gap-3 text-left focus-visible:outline-none"
            tabIndex={-1}
            aria-hidden="true"
          >
            <div className="flex items-center justify-between gap-3">
              <StatusBadge status={inspection.status} />
              <span className="font-medium tabular-nums">
                {formatFee(inspection.total_fee)}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {formatScheduledAt(inspection.scheduled_at)}
            </p>
            <InspectionTypePills types={inspection.inspection_types} />
          </button>
        </div>
      ))}
    </div>
  )
}
