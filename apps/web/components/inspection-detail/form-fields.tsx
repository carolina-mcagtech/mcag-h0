"use client"

import { Field, FieldLabel, FieldContent } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type Option = { value: string; label: string }

export function TextField({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string
  value: string | null
  onChange: (v: string | null) => void
  type?: "text" | "tel" | "email" | "date" | "datetime-local"
  placeholder?: string
}) {
  const id = `f-${label.replace(/\s+/g, "-").toLowerCase()}`
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Input
        id={id}
        type={type}
        value={value ?? ""}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value === "" ? null : e.target.value)}
      />
    </Field>
  )
}

export function NumberField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: number | null
  onChange: (v: number | null) => void
  placeholder?: string
}) {
  const id = `f-${label.replace(/\s+/g, "-").toLowerCase()}`
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Input
        id={id}
        type="number"
        inputMode="numeric"
        value={value ?? ""}
        placeholder={placeholder}
        onChange={(e) =>
          onChange(e.target.value === "" ? null : Number(e.target.value))
        }
      />
    </Field>
  )
}

export function CurrencyField({
  label,
  value,
  onChange,
}: {
  label: string
  value: number | null
  onChange: (v: number | null) => void
}) {
  const id = `f-${label.replace(/\s+/g, "-").toLowerCase()}`
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <div className="relative">
        <span className="pointer-events-none absolute top-1/2 left-2.5 -translate-y-1/2 text-sm text-muted-foreground">
          $
        </span>
        <Input
          id={id}
          type="number"
          inputMode="decimal"
          step="0.01"
          className="pl-6"
          value={value ?? ""}
          onChange={(e) =>
            onChange(e.target.value === "" ? null : Number(e.target.value))
          }
        />
      </div>
    </Field>
  )
}

export function SelectField({
  label,
  value,
  onChange,
  options,
  placeholder = "Select…",
}: {
  label: string
  value: string | null
  onChange: (v: string | null) => void
  options: readonly Option[]
  placeholder?: string
}) {
  return (
    <Field>
      <FieldLabel>{label}</FieldLabel>
      <Select
        value={value ?? ""}
        onValueChange={(v) => onChange(v || null)}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </Field>
  )
}

export function TextareaField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string | null
  onChange: (v: string | null) => void
  placeholder?: string
}) {
  const id = `f-${label.replace(/\s+/g, "-").toLowerCase()}`
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Textarea
        id={id}
        rows={4}
        value={value ?? ""}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value === "" ? null : e.target.value)}
      />
    </Field>
  )
}

export function SwitchField({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description?: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <Field orientation="horizontal" className="rounded-lg border p-3.5">
      <FieldContent>
        <FieldLabel className="font-medium">{label}</FieldLabel>
        {description ? (
          <p className="text-sm text-muted-foreground">{description}</p>
        ) : null}
      </FieldContent>
      <Switch checked={checked} onCheckedChange={onChange} />
    </Field>
  )
}
