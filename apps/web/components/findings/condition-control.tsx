"use client"

import { CONDITIONS, CONDITION_LABELS, type Condition } from "@/lib/findings"
import { cn } from "@/lib/utils"

const CONDITION_STYLES: Record<
  Condition,
  { active: string; idle: string; dot: string }
> = {
  GOOD: {
    active: "bg-emerald-600 text-white border-emerald-600",
    idle: "text-emerald-700 hover:bg-emerald-50 border-border",
    dot: "bg-emerald-600",
  },
  MARGINAL: {
    active: "bg-amber-500 text-white border-amber-500",
    idle: "text-amber-700 hover:bg-amber-50 border-border",
    dot: "bg-amber-500",
  },
  DEFECTIVE: {
    active: "bg-red-600 text-white border-red-600",
    idle: "text-red-700 hover:bg-red-50 border-border",
    dot: "bg-red-600",
  },
  N_A: {
    active: "bg-slate-500 text-white border-slate-500",
    idle: "text-slate-600 hover:bg-slate-100 border-border",
    dot: "bg-slate-400",
  },
}

interface ConditionControlProps {
  value?: Condition | null
  onChange: (value: Condition) => void
  invalid?: boolean
  id?: string
}

export function ConditionControl({ value, onChange, invalid, id }: ConditionControlProps) {
  return (
    <div
      id={id}
      role="radiogroup"
      aria-label="Condition"
      className={cn(
        "inline-flex flex-wrap gap-1 rounded-lg border p-1",
        invalid ? "border-destructive" : "border-input",
      )}
    >
      {CONDITIONS.map((c) => {
        const styles = CONDITION_STYLES[c]
        const active = value === c
        return (
          <button
            key={c}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(c)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
              active ? styles.active : cn("bg-background", styles.idle),
            )}
          >
            <span
              className={cn(
                "size-1.5 rounded-full",
                active ? "bg-current" : styles.dot,
              )}
              aria-hidden="true"
            />
            {CONDITION_LABELS[c]}
          </button>
        )
      })}
    </div>
  )
}

export function ConditionChip({ value }: { value?: Condition | null }) {
  if (!value) {
    return <span className="text-xs text-muted-foreground">—</span>
  }
  const styles = CONDITION_STYLES[value]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        styles.active,
      )}
    >
      {CONDITION_LABELS[value]}
    </span>
  )
}
