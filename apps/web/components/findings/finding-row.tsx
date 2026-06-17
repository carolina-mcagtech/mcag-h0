"use client"

import { useEffect, useState } from "react"
import { Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { ConditionControl } from "@/components/findings/condition-control"
import {
  SECTION_CONFIG,
  type Condition,
  type Finding,
} from "@/lib/findings"
import { cn } from "@/lib/utils"

interface FindingRowProps {
  finding: Finding
  index: number
  errors: { item?: string; condition?: string }
  onChange: (patch: Omit<Partial<Finding>, "saveStatus" | "id">) => void
  onRemove: () => void
  onRetry: () => void
}

function SaveStatusBadge({
  saveStatus,
  onRetry,
}: {
  saveStatus: Finding["saveStatus"]
  onRetry: () => void
}) {
  // "Saved ✓" fades after 2.5 s
  const [showSaved, setShowSaved] = useState(false)

  useEffect(() => {
    if (saveStatus === "saved") {
      setShowSaved(true)
      const t = setTimeout(() => setShowSaved(false), 2500)
      return () => clearTimeout(t)
    }
    setShowSaved(false)
  }, [saveStatus])

  if (saveStatus === "saving") {
    return (
      <span className="text-xs text-muted-foreground" aria-live="polite">
        Saving…
      </span>
    )
  }
  if (saveStatus === "error") {
    return (
      <button
        type="button"
        onClick={onRetry}
        className="text-xs text-amber-600 underline-offset-2 hover:underline"
        aria-live="polite"
      >
        ⚠ Retry
      </button>
    )
  }
  if (showSaved) {
    return (
      <span className="text-xs text-emerald-600 transition-opacity" aria-live="polite">
        Saved ✓
      </span>
    )
  }
  return null
}

export function FindingRow({ finding, index, errors, onChange, onRemove, onRetry }: FindingRowProps) {
  const config = SECTION_CONFIG[finding.section]
  const showCondition = config.conditionRule !== "forbidden"
  const conditionRequired = config.conditionRule === "required"

  const itemId = `item-${finding.id}`
  const obsId = `obs-${finding.id}`
  const costId = `cost-${finding.id}`

  return (
    <li className="rounded-lg border border-border bg-card p-4 shadow-xs">
      <div className="flex items-start justify-between gap-3">
        <span className="mt-1 inline-flex size-6 shrink-0 items-center justify-center rounded-md bg-secondary text-xs font-semibold text-secondary-foreground tabular-nums">
          {index + 1}
        </span>
        <div className="flex-1 space-y-4">
          {/* Item — required everywhere */}
          <div className="space-y-1.5">
            <label htmlFor={itemId} className="text-sm font-medium">
              Item <span className="text-destructive">*</span>
            </label>
            <Input
              id={itemId}
              value={finding.item}
              onChange={(e) => onChange({ item: e.target.value })}
              placeholder="e.g. Roof covering"
              aria-invalid={!!errors.item}
              aria-describedby={errors.item ? `${itemId}-error` : undefined}
            />
            {errors.item && (
              <p id={`${itemId}-error`} className="text-xs text-destructive">
                {errors.item}
              </p>
            )}
          </div>

          {/* Condition — only for sections where it is not forbidden */}
          {showCondition && (
            <div className="space-y-1.5">
              <label className="text-sm font-medium">
                Condition{" "}
                {conditionRequired ? (
                  <span className="text-destructive">*</span>
                ) : (
                  <span className="text-xs font-normal text-muted-foreground">(optional)</span>
                )}
              </label>
              <div>
                <ConditionControl
                  value={finding.condition}
                  onChange={(c: Condition) => onChange({ condition: c })}
                  invalid={!!errors.condition}
                />
              </div>
              {errors.condition && (
                <p className="text-xs text-destructive">{errors.condition}</p>
              )}
            </div>
          )}

          {/* Observations — optional everywhere */}
          <div className="space-y-1.5">
            <label htmlFor={obsId} className="text-sm font-medium">
              Observations
            </label>
            <Textarea
              id={obsId}
              value={finding.observations ?? ""}
              onChange={(e) => onChange({ observations: e.target.value })}
              placeholder="Free-text notes…"
              rows={2}
            />
          </div>

          {/* Estimated cost — ONLY for COST_ESTIMATION */}
          {config.showEstimatedCost && (
            <div className="space-y-1.5">
              <label htmlFor={costId} className="text-sm font-medium">
                Estimated cost
              </label>
              <div className="relative w-48">
                <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                  $
                </span>
                <Input
                  id={costId}
                  type="number"
                  min={0}
                  step={50}
                  className={cn("pl-7")}
                  value={finding.estimated_cost ?? ""}
                  onChange={(e) =>
                    onChange({
                      estimated_cost: e.target.value === "" ? null : Number(e.target.value),
                    })
                  }
                  placeholder="0"
                />
              </div>
            </div>
          )}
        </div>

        {/* Status badge + delete button */}
        <div className="flex shrink-0 items-center gap-2 pt-0.5">
          <SaveStatusBadge saveStatus={finding.saveStatus} onRetry={onRetry} />
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={onRemove}
            aria-label={`Remove finding ${index + 1}`}
            className="text-muted-foreground hover:text-destructive"
          >
            <Trash2 />
          </Button>
        </div>
      </div>
    </li>
  )
}
