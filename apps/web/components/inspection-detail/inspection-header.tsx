"use client"

import { CheckIcon, FileEditIcon, MapPinIcon, SaveIcon } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  INSPECTION_STATUS_META,
  type InspectionStatus,
} from "@/lib/inspection-detail"

export function InspectionHeader({
  address,
  status,
  isDirty,
  onSave,
  onEditFindings,
}: {
  address: string
  status: InspectionStatus
  isDirty: boolean
  onSave: () => void
  onEditFindings: () => void
}) {
  const statusMeta = INSPECTION_STATUS_META[status]

  return (
    <header className="flex flex-col gap-4 border-b border-border pb-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-foreground">
              <MapPinIcon className="size-5 shrink-0 text-muted-foreground" />
              {address}
            </h1>
            <Badge
              variant="outline"
              className={cn("font-medium", statusMeta.className)}
            >
              {statusMeta.label}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Review and edit all details for this property inspection.
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button variant="outline" onClick={onEditFindings}>
            <FileEditIcon data-icon="inline-start" />
            Edit Findings
          </Button>
          <Button onClick={onSave} disabled={!isDirty}>
            <SaveIcon data-icon="inline-start" />
            Save Changes
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-1.5 text-sm">
        {isDirty ? (
          <span className="flex items-center gap-1.5 text-amber-700">
            <span className="size-2 rounded-full bg-amber-500" />
            Unsaved changes
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <CheckIcon className="size-3.5 text-green-600" />
            All changes saved
          </span>
        )}
      </div>
    </header>
  )
}
