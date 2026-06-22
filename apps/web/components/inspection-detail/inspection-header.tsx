"use client"

import { ArrowLeftIcon, CheckIcon, DownloadIcon, FileEditIcon, FileTextIcon, MapPinIcon } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  INSPECTION_STATUS_META,
  type InspectionStatus,
} from "@/lib/inspection-detail"
import type { SaveStatus, TransitionStatus } from "@/hooks/use-inspection-detail"

const TRANSITION_CONFIG: Partial<
  Record<InspectionStatus, { label: string; next: string; className: string }>
> = {
  DRAFT: {
    label: "Start Inspection",
    next: "IN_FIELD",
    className: "",
  },
  IN_FIELD: {
    label: "Submit for Review",
    next: "PENDING_REVIEW",
    className: "",
  },
  PENDING_REVIEW: {
    label: "Publish Report",
    next: "PUBLISHED",
    className: "bg-green-600 text-white hover:bg-green-700 border-green-600",
  },
  PUBLISHED: {
    label: "Mark Delivered",
    next: "DELIVERED",
    className: "bg-teal-600 text-white hover:bg-teal-700 border-teal-600",
  },
}

export function InspectionHeader({
  address,
  status,
  inspectionId,
  saveStatus,
  transitionStatus,
  transitionError,
  onBack,
  onEditFindings,
  onTransition,
}: {
  address: string
  status: InspectionStatus
  inspectionId: string
  saveStatus: SaveStatus
  transitionStatus: TransitionStatus
  transitionError: string | null
  onBack: () => void
  onEditFindings: () => void
  onTransition: (nextStatus: string) => void
}) {
  const statusMeta = INSPECTION_STATUS_META[status]
  const txConfig = TRANSITION_CONFIG[status]

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
              ) : saveStatus === "warning" ? (
                <span className="text-amber-600">This inspection is delivered and cannot be edited.</span>
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

        <div className="flex shrink-0 flex-col items-end gap-1">
          <div className="flex items-center gap-2">
            {txConfig && (
              <Button
                size="sm"
                disabled={transitionStatus === "loading"}
                onClick={() => onTransition(txConfig.next)}
                className={txConfig.className}
              >
                {transitionStatus === "loading" ? "Updating…" : txConfig.label}
              </Button>
            )}
            <Button size="sm" variant="outline" title="Edit Findings" onClick={onEditFindings}>
              <FileEditIcon data-icon="inline-start" />
              <span className="hidden md:inline">Edit Findings</span>
            </Button>
            <a
              href={`/api/inspections/${inspectionId}/agreement`}
              download="inspection-agreement.pdf"
              title="Send Agreement"
              className={cn(buttonVariants({ size: "sm", variant: "outline" }))}
            >
              <FileTextIcon data-icon="inline-start" />
              <span className="hidden md:inline">Send Agreement</span>
            </a>
            <a
              href={`/api/inspections/${inspectionId}/report`}
              download
              title="Download Report"
              className={cn(buttonVariants({ size: "sm", variant: "outline" }))}
            >
              <DownloadIcon data-icon="inline-start" />
              <span className="hidden md:inline">Download Report</span>
            </a>
          </div>
          {transitionStatus === "error" && transitionError && (
            <p className="text-xs text-destructive">{transitionError}</p>
          )}
        </div>
      </div>
    </header>
  )
}
