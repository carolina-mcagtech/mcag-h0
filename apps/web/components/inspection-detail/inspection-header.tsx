"use client"

import { ArrowLeftIcon, CheckIcon, FileEditIcon, MapPinIcon } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  INSPECTION_STATUS_META,
  type InspectionStatus,
} from "@/lib/inspection-detail"
import type { SaveStatus } from "@/hooks/use-inspection-detail"

export function InspectionHeader({
  address,
  status,
  saveStatus,
  onBack,
  onEditFindings,
}: {
  address: string
  status: InspectionStatus
  saveStatus: SaveStatus
  onBack: () => void
  onEditFindings: () => void
}) {
  const statusMeta = INSPECTION_STATUS_META[status]

  return (
    <header className="flex flex-col gap-4 border-b border-border pb-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="ghost" size="sm" onClick={onBack} className="-ml-1">
              <ArrowLeftIcon data-icon="inline-start" />
              Back
            </Button>
            <Badge
              variant="outline"
              className={cn("font-medium", statusMeta.className)}
            >
              {statusMeta.label}
            </Badge>
          </div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-foreground">
            <MapPinIcon className="size-5 shrink-0 text-muted-foreground" />
            {address}
          </h1>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button variant="outline" onClick={onEditFindings}>
            <FileEditIcon data-icon="inline-start" />
            Edit Findings
          </Button>
        </div>
      </div>

      {saveStatus !== "idle" && (
        <div className="flex items-center gap-1.5 text-sm">
          {saveStatus === "saving" ? (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <span className="size-2 animate-pulse rounded-full bg-primary" />
              Saving…
            </span>
          ) : saveStatus === "error" ? (
            <span className="text-destructive">Save failed — will retry on next change</span>
          ) : (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <CheckIcon className="size-3.5 text-green-600" />
              All changes saved
            </span>
          )}
        </div>
      )}
    </header>
  )
}
