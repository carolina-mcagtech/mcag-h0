"use client"

import { CheckIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { Field, FieldLabel, FieldError } from "@/components/ui/field"
import {
  INSPECTION_TYPE_OPTIONS,
  type InspectionTypeValue,
} from "@/lib/inspection-detail"

export function InspectionTypesField({
  value,
  onChange,
  disabled,
}: {
  value: InspectionTypeValue[]
  onChange: (v: InspectionTypeValue[]) => void
  disabled?: boolean
}) {
  function toggle(option: InspectionTypeValue) {
    if (disabled) return
    if (value.includes(option)) {
      onChange(value.filter((v) => v !== option))
    } else {
      onChange([...value, option])
    }
  }

  const invalid = value.length === 0

  return (
    <Field data-invalid={invalid || undefined}>
      <FieldLabel>
        Inspection Types <span className="text-destructive">*</span>
      </FieldLabel>
      <div className={cn("flex flex-wrap gap-2", disabled && "opacity-60 pointer-events-none")}>
        {INSPECTION_TYPE_OPTIONS.map((opt) => {
          const selected = value.includes(opt.value)
          return (
            <button
              key={opt.value}
              type="button"
              aria-pressed={selected}
              disabled={disabled}
              onClick={() => toggle(opt.value)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
                selected
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-input bg-background text-foreground hover:bg-accent hover:text-accent-foreground",
              )}
            >
              {selected ? <CheckIcon className="size-3.5" /> : null}
              {opt.label}
            </button>
          )
        })}
      </div>
      {invalid ? (
        <FieldError>Select at least one inspection type.</FieldError>
      ) : null}
    </Field>
  )
}
