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
    <header className="border-b border-border bg-card">
      <div className="flex items-center gap-2 px-4 py-3 md:px-6 md:py-4">
        <Button variant="ghost" size="sm" onClick={onBack} className="-ml-1 shrink-0">
          <ArrowLeftIcon data-icon="inline-start" />
          Back
        </Button>

        <div className="flex min-w-0 flex-1 flex-col justify-center gap-0.5">
          <div className="flex items-center gap-2">
            <MapPinIcon className="size-4 shrink-0 text-muted-foreground" />
            <h1 className="truncate text-base font-semibold text-foreground">{address}</h1>
            <Badge
              variant="outline"
              className={cn("shrink-0 font-medium", statusMeta.className)}
            >
              {statusMeta.label}
            </Badge>
          </div>
          {saveStatus !== "idle" && (
            <p className="flex items-center gap-1 pl-6 text-xs">
              {saveStatus === "saving" ? (
                <span className="flex items-center gap-1 text-muted-foreground">
                  <span className="size-1.5 animate-pulse rounded-full bg-primary" />
                  Saving…
                </span>
              ) : saveStatus === "error" ? (
                <span className="text-destructive">Save failed</span>
              ) : (
                <span className="flex items-center gap-1 text-muted-foreground">
                  <CheckIcon className="size-3 text-green-600" />
                  All changes saved
                </span>
              )}
            </p>
          )}
        </div>

        <Button size="sm" variant="outline" onClick={onEditFindings} className="shrink-0">
          <FileEditIcon data-icon="inline-start" />
          Edit Findings
        </Button>
      </div>
    </header>
  )
}
