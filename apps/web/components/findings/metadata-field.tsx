"use client"

import { Input } from "@/components/ui/input"
import type { CatalogMetadataField } from "@/lib/observations"
import { cn } from "@/lib/utils"

interface MetadataFieldProps {
  fieldKey: string
  field: CatalogMetadataField
  value: unknown
  onChange: (value: unknown) => void
}

export function MetadataField({ fieldKey, field, value, onChange }: MetadataFieldProps) {
  const id = `meta-${fieldKey}`

  if (field.type === "text") {
    return (
      <div className="space-y-1.5">
        <label htmlFor={id} className="text-xs font-medium text-muted-foreground">
          {field.label}
        </label>
        <Input
          id={id}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.label}
          className="h-7 text-sm"
        />
      </div>
    )
  }

  if (field.type === "number") {
    const isTempField = field.label.includes("°F") || field.label.toLowerCase().includes("temp")
    return (
      <div className="space-y-1.5">
        <label htmlFor={id} className="text-xs font-medium text-muted-foreground">
          {field.label}
        </label>
        <div className="relative w-28">
          <Input
            id={id}
            type="number"
            value={typeof value === "number" ? value : ""}
            onChange={(e) =>
              onChange(e.target.value === "" ? null : Number(e.target.value))
            }
            placeholder="0"
            className={cn("h-7 text-sm", isTempField && "pr-8")}
          />
          {isTempField && (
            <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
              °F
            </span>
          )}
        </div>
      </div>
    )
  }

  if (field.type === "select") {
    const options = field.options ?? []
    const current = typeof value === "string" ? value : null
    return (
      <div className="space-y-1.5">
        <span className="text-xs font-medium text-muted-foreground">{field.label}</span>
        <div className="flex flex-wrap gap-1.5">
          {options.map((opt) => {
            const active = current === opt
            return (
              <button
                key={opt}
                type="button"
                onClick={() => onChange(active ? null : opt)}
                className={cn(
                  "rounded-full border px-3 py-0.5 text-xs font-medium transition-colors",
                  active
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-background text-muted-foreground hover:bg-accent",
                )}
              >
                {opt}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  // multiselect
  const options = field.options ?? []
  const current: string[] = Array.isArray(value) ? (value as string[]) : []
  return (
    <div className="space-y-1.5">
      <span className="text-xs font-medium text-muted-foreground">{field.label}</span>
      <div className="flex flex-wrap gap-1.5">
        {options.map((opt) => {
          const active = current.includes(opt)
          return (
            <button
              key={opt}
              type="button"
              onClick={() => {
                const next = active
                  ? current.filter((v) => v !== opt)
                  : [...current, opt]
                onChange(next)
              }}
              className={cn(
                "rounded-full border px-3 py-0.5 text-xs font-medium transition-colors",
                active
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-background text-muted-foreground hover:bg-accent",
              )}
            >
              {opt}
            </button>
          )
        })}
      </div>
    </div>
  )
}
