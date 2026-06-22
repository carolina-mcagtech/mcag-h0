"use client"

import { useRouter } from "next/navigation"
import { Trash2 } from "lucide-react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  formatFee,
  formatScheduledAt,
  type Inspection,
} from "@/lib/inspections"
import { StatusBadge } from "./status-badge"
import { InspectionTypePills } from "./inspection-type-pills"

export function InspectionsTable({
  inspections,
  onDelete,
}: {
  inspections: Inspection[]
  onDelete?: (id: string) => void
}) {
  const router = useRouter()

  function goToDetail(id: string) {
    router.push(`/inspections/${id}`)
  }

  return (
    <div className="hidden overflow-hidden rounded-lg border border-border bg-card md:block">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            <TableHead className="pl-6">Property Address</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Scheduled</TableHead>
            <TableHead>Inspection Types</TableHead>
            <TableHead className="text-right">Fee</TableHead>
            <TableHead className="w-12 pr-4" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {inspections.map((inspection) => (
            <TableRow
              key={inspection.id}
              onClick={() => goToDetail(inspection.id)}
              tabIndex={0}
              role="link"
              aria-label={`View inspection at ${inspection.property_address}`}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault()
                  goToDetail(inspection.id)
                }
              }}
              className="cursor-pointer transition-colors hover:bg-accent/50 focus-visible:bg-accent/50 focus-visible:outline-none"
            >
              <TableCell className="pl-6 font-semibold text-foreground">
                {inspection.property_address}
              </TableCell>
              <TableCell>
                <StatusBadge status={inspection.status} />
              </TableCell>
              <TableCell className="whitespace-nowrap text-muted-foreground">
                {formatScheduledAt(inspection.scheduled_at)}
              </TableCell>
              <TableCell>
                <InspectionTypePills types={inspection.inspection_types} />
              </TableCell>
              <TableCell className="text-right font-medium tabular-nums">
                {formatFee(inspection.total_fee)}
              </TableCell>
              <TableCell className="pr-4 text-right">
                {onDelete && (
                  <button
                    type="button"
                    aria-label={`Delete inspection at ${inspection.property_address}`}
                    onClick={(e) => { e.stopPropagation(); onDelete(inspection.id) }}
                    className="inline-flex size-7 items-center justify-center rounded-md text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring group-hover:opacity-100 [tr:hover_&]:opacity-100"
                  >
                    <Trash2 className="size-3.5" />
                  </button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
