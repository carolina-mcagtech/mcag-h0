"use client"

import { useRouter } from "next/navigation"
import { ChevronRight } from "lucide-react"
import {
  formatFee,
  formatScheduledAt,
  type Inspection,
} from "@/lib/inspections"
import { StatusBadge } from "./status-badge"
import { InspectionTypePills } from "./inspection-type-pills"

export function InspectionsCards({
  inspections,
}: {
  inspections: Inspection[]
}) {
  const router = useRouter()

  return (
    <div className="flex flex-col gap-3 md:hidden">
      {inspections.map((inspection) => (
        <button
          key={inspection.id}
          type="button"
          onClick={() => router.push(`/inspections/${inspection.id}`)}
          className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 text-left transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label={`View inspection at ${inspection.property_address}`}
        >
          <div className="flex items-start justify-between gap-3">
            <span className="font-semibold leading-snug text-foreground">
              {inspection.property_address}
            </span>
            <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          </div>
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
      ))}
    </div>
  )
}
