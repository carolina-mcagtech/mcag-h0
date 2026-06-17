import { INSPECTION_TYPE_LABELS, type InspectionType } from "@/lib/inspections"

export function InspectionTypePills({ types }: { types: InspectionType[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {types.map((type) => (
        <span
          key={type}
          className="inline-flex items-center rounded-md border border-border bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground"
        >
          {INSPECTION_TYPE_LABELS[type]}
        </span>
      ))}
    </div>
  )
}
