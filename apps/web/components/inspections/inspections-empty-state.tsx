import { ClipboardList, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

export function InspectionsEmptyState({
  onNewInspection,
}: {
  onNewInspection?: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-border bg-card px-6 py-20 text-center">
      <div className="flex size-14 items-center justify-center rounded-full bg-secondary text-primary">
        <ClipboardList className="size-7" aria-hidden="true" />
      </div>
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold text-foreground">
          No inspections yet
        </h2>
        <p className="max-w-sm text-sm text-muted-foreground text-pretty">
          When you schedule your first inspection, it will appear here. Get
          started by creating a new inspection.
        </p>
      </div>
      <Button onClick={onNewInspection}>
        <Plus className="size-4" aria-hidden="true" />
        New Inspection
      </Button>
    </div>
  )
}
