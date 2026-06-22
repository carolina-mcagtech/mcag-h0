"use client"

import { useState } from "react"
import { useFindings } from "@/hooks/use-findings"
import { PageHeader } from "@/components/findings/page-header"
import { SectionSidebar } from "@/components/findings/section-sidebar"
import { SectionPanel } from "@/components/findings/section-panel"
import { type Finding, type InspectionMeta, type Section } from "@/lib/findings"
import { type SectionCatalog, FINDINGS_TO_CATALOG_SECTION } from "@/lib/observations"
import { cn } from "@/lib/utils"

function resolveCatalogSections(activeSection: Section): string[] {
  const raw = FINDINGS_TO_CATALOG_SECTION[activeSection] ?? null
  if (raw === null) return []
  return Array.isArray(raw) ? raw : [raw]
}

interface FindingsEntryProps {
  initialFindings: Finding[]
  inspection: InspectionMeta
  catalogData: Record<string, SectionCatalog>
  numBedrooms: number
  numBathrooms: number
}

export function FindingsEntry({
  initialFindings,
  inspection,
  catalogData,
  numBedrooms,
  numBathrooms,
}: FindingsEntryProps) {
  const {
    findingsBySection,
    counts,
    sectionsWithErrors,
    globalSaveStatus,
    addFinding,
    updateFinding,
    updateFindingLocalOnly,
    removeFinding,
    retryFinding,
  } = useFindings(initialFindings, inspection)

  const [activeSection, setActiveSection] = useState<Section>("ROOF")
  const [showMobilePanel, setShowMobilePanel] = useState(false)
  const [observedSections, setObservedSections] = useState<Set<Section>>(new Set())

  const isReadOnly =
    inspection.status === "DELIVERED" || inspection.status === "PUBLISHED"

  const handleSelectSection = (section: Section) => {
    setActiveSection(section)
    setShowMobilePanel(true)
  }

  const handleObservationsLoaded = (section: Section) => {
    setObservedSections((prev) => {
      if (prev.has(section)) return prev
      return new Set([...prev, section])
    })
  }

  return (
    <div className="flex h-dvh flex-col bg-background">
      <PageHeader
        inspection={inspection}
        globalSaveStatus={globalSaveStatus}
      />

      {isReadOnly && (
        <div className="border-b border-amber-200 bg-amber-50 px-6 py-2.5 text-sm text-amber-800">
          This inspection has been delivered and is read-only.
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <aside
          className={cn(
            "shrink-0 overflow-y-auto border-r border-border bg-sidebar",
            "w-full md:w-64",
            showMobilePanel ? "hidden md:block" : "block",
          )}
        >
          <SectionSidebar
            active={activeSection}
            onSelect={handleSelectSection}
            counts={counts}
            sectionsWithErrors={sectionsWithErrors}
            observedSections={observedSections}
          />
        </aside>

        <main
          className={cn(
            "min-w-0 flex-1 overflow-hidden",
            showMobilePanel ? "block" : "hidden md:block",
          )}
        >
          <SectionPanel
            section={activeSection}
            findings={findingsBySection[activeSection] ?? []}
            onAdd={() => addFinding(activeSection)}
            onUpdate={updateFinding}
            onRemove={removeFinding}
            onRetry={retryFinding}
            onPhotosChange={(id, photos) => updateFindingLocalOnly(id, { photos })}
            onMobileBack={() => setShowMobilePanel(false)}
            inspectionId={inspection.id}
            catalogSections={resolveCatalogSections(activeSection)}
            catalogData={catalogData}
            numBedrooms={numBedrooms}
            numBathrooms={numBathrooms}
            isReadOnly={isReadOnly}
            onObservationsLoaded={handleObservationsLoaded}
          />
        </main>
      </div>
    </div>
  )
}
