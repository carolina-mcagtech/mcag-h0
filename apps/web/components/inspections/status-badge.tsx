import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { STATUS_LABELS, type InspectionStatus } from "@/lib/inspections"

const STATUS_STYLES: Record<InspectionStatus, string> = {
  DRAFT: "border-slate-200 bg-slate-100 text-slate-600",
  IN_FIELD: "border-blue-200 bg-blue-50 text-blue-700",
  PENDING_REVIEW: "border-amber-200 bg-amber-50 text-amber-700",
  PUBLISHED: "border-green-200 bg-green-50 text-green-700",
  DELIVERED: "border-emerald-200 bg-emerald-50 text-emerald-700",
}

export function StatusBadge({ status }: { status: InspectionStatus }) {
  return (
    <Badge
      variant="outline"
      className={cn("font-medium", STATUS_STYLES[status])}
    >
      {STATUS_LABELS[status]}
    </Badge>
  )
}
