"use client"

import { useState } from "react"
import { useFindings } from "@/hooks/use-findings"
import { PageHeader } from "@/components/findings/page-header"
import { SectionSidebar } from "@/components/findings/section-sidebar"
import { SectionPanel } from "@/components/findings/section-panel"
import { type Finding, type InspectionMeta, type Section } from "@/lib/findings"

interface FindingsEntryProps {
  initialFindings: Finding[]
  inspection: InspectionMeta
}

export function FindingsEntry({ initialFindings, inspection }: FindingsEntryProps) {
  const {
    findingsBySection,
    counts,
    sectionsWithErrors,
    globalSaveStatus,
    addFinding,
    updateFinding,
    removeFinding,
    retryFinding,
    flushAll,
  } = useFindings(initialFindings, inspection)

  const [activeSection, setActiveSection] = useState<Section>("ROOF")

  return (
    <div className="flex h-dvh flex-col bg-background">
      <PageHeader
        inspection={inspection}
        globalSaveStatus={globalSaveStatus}
        onFlush={flushAll}
      />

      <div className="flex min-h-0 flex-1">
        <aside className="w-64 shrink-0 overflow-y-auto border-r border-border bg-sidebar">
          <SectionSidebar
            active={activeSection}
            onSelect={setActiveSection}
            counts={counts}
            sectionsWithErrors={sectionsWithErrors}
          />
        </aside>

        <main className="min-w-0 flex-1 overflow-hidden">
          <SectionPanel
            section={activeSection}
            findings={findingsBySection[activeSection] ?? []}
            onAdd={() => addFinding(activeSection)}
            onUpdate={updateFinding}
            onRemove={removeFinding}
            onRetry={retryFinding}
          />
        </main>
      </div>
    </div>
  )
}
