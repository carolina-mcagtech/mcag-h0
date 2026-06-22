import { Fragment } from "react"
import { INSPECTION_TYPE_LABELS, type InspectionType } from "@/lib/inspections"

export function InspectionTypePills({ types }: { types: InspectionType[] }) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      {types.map((type, i) => (
        <Fragment key={type}>
          {i > 0 && (
            <span className="select-none text-xs text-muted-foreground">·</span>
          )}
          <span className="inline-flex items-center rounded-md border border-border bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground">
            {INSPECTION_TYPE_LABELS[type]}
          </span>
        </Fragment>
      ))}
    </div>
  )
}
