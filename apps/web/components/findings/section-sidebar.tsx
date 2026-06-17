"use client"

import { AlertCircle } from "lucide-react"
import { SECTIONS, SECTION_LABELS, type Section } from "@/lib/findings"
import { cn } from "@/lib/utils"

interface SectionSidebarProps {
  active: Section
  onSelect: (section: Section) => void
  counts: Record<Section, number>
  sectionsWithErrors: Set<Section>
}

export function SectionSidebar({
  active,
  onSelect,
  counts,
  sectionsWithErrors,
}: SectionSidebarProps) {
  return (
    <nav aria-label="Inspection sections" className="flex flex-col gap-0.5 p-2">
      <p className="px-2 pb-1.5 pt-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Sections
      </p>
      {SECTIONS.map((section) => {
        const count = counts[section] ?? 0
        const isActive = section === active
        const hasError = sectionsWithErrors.has(section)
        return (
          <button
            key={section}
            type="button"
            onClick={() => onSelect(section)}
            aria-current={isActive ? "true" : undefined}
            className={cn(
              "group flex items-center justify-between gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
              isActive
                ? "bg-sidebar-primary text-sidebar-primary-foreground"
                : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            )}
          >
            <span className="flex items-center gap-2 truncate">
              <span className="truncate font-medium">{SECTION_LABELS[section]}</span>
              {hasError && (
                <AlertCircle
                  className={cn(
                    "size-3.5 shrink-0",
                    isActive ? "text-amber-200" : "text-amber-500",
                  )}
                  aria-label="Has findings missing required fields"
                />
              )}
            </span>
            <span
              className={cn(
                "inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-semibold tabular-nums",
                isActive
                  ? "bg-sidebar-primary-foreground/20 text-sidebar-primary-foreground"
                  : count > 0
                    ? "bg-secondary text-secondary-foreground"
                    : "text-muted-foreground",
              )}
            >
              {count}
            </span>
          </button>
        )
      })}
    </nav>
  )
}
