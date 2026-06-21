"use client"

import { useState } from "react"
import { useFindings } from "@/hooks/use-findings"
import { PageHeader } from "@/components/findings/page-header"
import { SectionSidebar } from "@/components/findings/section-sidebar"
import { SectionPanel } from "@/components/findings/section-panel"
import { type Finding, type InspectionMeta, type Section } from "@/lib/findings"
import { type SectionCatalog } from "@/lib/observations"
import { cn } from "@/lib/utils"

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
    removeFinding,
    retryFinding,
  } = useFindings(initialFindings, inspection)

  const [activeSection, setActiveSection] = useState<Section>("ROOF")
  const [showMobilePanel, setShowMobilePanel] = useState(false)

  const handleSelectSection = (section: Section) => {
    setActiveSection(section)
    setShowMobilePanel(true)
  }

  return (
    <div className="flex h-dvh flex-col bg-background">
      <PageHeader
        inspection={inspection}
        globalSaveStatus={globalSaveStatus}
      />

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
            onMobileBack={() => setShowMobilePanel(false)}
            inspectionId={inspection.id}
            sectionCatalog={catalogData[activeSection]}
            numBedrooms={numBedrooms}
            numBathrooms={numBathrooms}
          />
        </main>
      </div>
    </div>
  )
}
