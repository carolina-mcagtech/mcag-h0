"use client"

import { ArrowLeftIcon, Plus, ClipboardList } from "lucide-react"
import { Button } from "@/components/ui/button"
import { FindingRow } from "@/components/findings/finding-row"
import { ObservationsPanel } from "@/components/findings/observations-panel"
import {
  SECTION_CONFIG,
  SECTION_LABELS,
  getFindingErrors,
  type Finding,
  type Photo,
  type Section,
} from "@/lib/findings"
import { type SectionCatalog } from "@/lib/observations"
import { cn } from "@/lib/utils"

interface SectionPanelProps {
  section: Section
  findings: Finding[]
  onAdd: () => void
  onUpdate: (id: string, patch: Omit<Partial<Finding>, "saveStatus" | "id">) => void
  onRemove: (id: string) => void
  onRetry: (id: string) => void
  onPhotosChange: (id: string, photos: Photo[]) => void
  onMobileBack: () => void
  inspectionId: string
  catalogSections: string[]
  catalogData: Record<string, SectionCatalog>
  numBedrooms: number
  numBathrooms: number
}

const RULE_BADGE: Record<string, { label: string; className: string }> = {
  required: {
    label: "Condition required",
    className: "bg-primary/10 text-primary",
  },
  optional: {
    label: "Condition optional",
    className: "bg-amber-100 text-amber-700",
  },
  forbidden: {
    label: "No condition rating",
    className: "bg-slate-100 text-slate-600",
  },
}

export function SectionPanel({
  section,
  findings,
  onAdd,
  onUpdate,
  onRemove,
  onRetry,
  onPhotosChange,
  onMobileBack,
  inspectionId,
  catalogSections,
  catalogData,
  numBedrooms,
  numBathrooms,
}: SectionPanelProps) {
  const config = SECTION_CONFIG[section]
  const rule = RULE_BADGE[config.conditionRule]

  return (
    <section className="flex h-full flex-col" aria-label={`${SECTION_LABELS[section]} findings`}>
      <header className="border-b border-border px-6 py-5">
        <Button
          variant="ghost"
          size="sm"
          onClick={onMobileBack}
          className="md:hidden -ml-2 mb-3"
        >
          <ArrowLeftIcon data-icon="inline-start" />
          Sections
        </Button>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-foreground">
                {SECTION_LABELS[section]}
              </h2>
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                  rule.className,
                )}
              >
                {rule.label}
              </span>
              {config.showEstimatedCost && (
                <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                  Cost field enabled
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{config.helper}</p>
          </div>
          <Button type="button" onClick={onAdd} size="sm">
            <Plus />
            Add finding
          </Button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-5">
        {/* ── Observations panels (stacked above findings) ──────────── */}
        {catalogSections.length > 0 && (
          <>
            {catalogSections.map((cs, idx) => {
              const catalog = catalogData[cs]
              if (!catalog) return null
              return (
                <div key={cs}>
                  {catalogSections.length > 1 && (
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {catalog.label}
                    </p>
                  )}
                  <ObservationsPanel
                    inspectionId={inspectionId}
                    section={cs}
                    catalog={catalog}
                    numBedrooms={numBedrooms}
                    numBathrooms={numBathrooms}
                  />
                  {idx < catalogSections.length - 1 && (
                    <div className="my-4 border-t border-border/60" />
                  )}
                </div>
              )
            })}
            <div className="my-5 border-t border-border" />
          </>
        )}

        {/* ── Findings list ─────────────────────────────────────────── */}
        {findings.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border py-16 text-center">
            <div className="flex size-11 items-center justify-center rounded-full bg-secondary text-muted-foreground">
              <ClipboardList className="size-5" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">No findings yet</p>
              <p className="text-sm text-muted-foreground">
                Add the first finding for {SECTION_LABELS[section]}.
              </p>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={onAdd}>
              <Plus />
              Add finding
            </Button>
          </div>
        ) : (
          <ul className="space-y-3">
            {findings.map((finding, index) => (
              <FindingRow
                key={finding.id}
                finding={finding}
                index={index}
                errors={getFindingErrors(finding)}
                inspectionId={inspectionId}
                onChange={(patch) => onUpdate(finding.id, patch)}
                onRemove={() => onRemove(finding.id)}
                onRetry={() => onRetry(finding.id)}
                onPhotosChange={(photos) => onPhotosChange(finding.id, photos)}
              />
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
