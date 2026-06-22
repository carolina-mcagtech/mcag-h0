"use client"

import { useEffect, useState } from "react"
import { useObservations } from "@/hooks/use-observations"
import { MetadataField } from "@/components/findings/metadata-field"
import { Input } from "@/components/ui/input"
import {
  CONDITIONS,
  CONDITION_LABELS,
  type ComponentCondition,
  type ComponentObservation,
  type SectionCatalog,
} from "@/lib/observations"
import { cn } from "@/lib/utils"

// Condition pill colors (softer palette — distinct from the findings ConditionControl)
const CONDITION_STYLES: Record<
  ComponentCondition,
  { active: string; idle: string }
> = {
  GOOD: {
    active: "bg-green-100 text-green-800 border-green-300",
    idle: "border-border text-muted-foreground hover:bg-accent",
  },
  MARGINAL: {
    active: "bg-yellow-100 text-yellow-800 border-yellow-300",
    idle: "border-border text-muted-foreground hover:bg-accent",
  },
  DEFECTIVE: {
    active: "bg-red-100 text-red-800 border-red-300",
    idle: "border-border text-muted-foreground hover:bg-accent",
  },
  N_A: {
    active: "bg-gray-100 text-gray-600 border-gray-300",
    idle: "border-border text-muted-foreground hover:bg-accent",
  },
}

function ItemSaveIndicator({ status }: { status: "idle" | "saving" | "saved" | "error" }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (status === "saved") {
      setVisible(true)
      const t = setTimeout(() => setVisible(false), 2000)
      return () => clearTimeout(t)
    }
    setVisible(false)
  }, [status])

  if (status === "saving") {
    return <span className="text-[10px] text-muted-foreground">Saving…</span>
  }
  if (status === "error") {
    return <span className="text-[10px] text-destructive">⚠ Error</span>
  }
  if (visible) {
    return <span className="text-[10px] text-emerald-600">✓</span>
  }
  return null
}

// One row per catalog item within a room (or the whole section for non-room sections)
function ObservationItemRow({
  itemKey,
  itemLabel,
  observation,
  roomIndex,
  roomLabel,
  saveStatus,
  onConditionChange,
  onNotesBlur,
}: {
  itemKey: string
  itemLabel: string
  observation: ComponentObservation | undefined
  roomIndex: number
  roomLabel: string | null
  saveStatus: "idle" | "saving" | "saved" | "error"
  onConditionChange: (condition: ComponentCondition) => void
  onNotesBlur: (notes: string) => void
}) {
  const currentCondition = observation?.condition ?? null
  const [notes, setNotes] = useState(observation?.observations ?? "")
  const [notesOpen, setNotesOpen] = useState(!!(observation?.observations))

  // Keep notes in sync when observation loads/changes from server
  useEffect(() => {
    setNotes(observation?.observations ?? "")
    setNotesOpen(!!(observation?.observations))
  }, [observation?.observations])

  return (
    <div className="group flex flex-col gap-1.5 rounded-md px-2 py-2 hover:bg-muted/30">
      <div className="flex flex-wrap items-center gap-2 md:flex-nowrap">
        {/* Label */}
        <span className="w-32 shrink-0 text-xs font-medium text-foreground md:w-36">
          {itemLabel}
        </span>

        {/* Condition pills */}
        <div className="flex flex-wrap gap-1 md:flex-nowrap">
          {CONDITIONS.map((c) => {
            const active = currentCondition === c
            const styles = CONDITION_STYLES[c]
            return (
              <button
                key={c}
                type="button"
                onClick={() => onConditionChange(c)}
                className={cn(
                  "rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-colors",
                  active ? styles.active : styles.idle,
                )}
              >
                {CONDITION_LABELS[c]}
              </button>
            )
          })}
        </div>

        {/* Notes toggle / inline input */}
        <div className="flex min-w-0 flex-1 items-center gap-1.5">
          {notesOpen ? (
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              onBlur={() => {
                if (!notes.trim()) setNotesOpen(false)
                onNotesBlur(notes)
              }}
              placeholder="Notes…"
              className="h-6 min-w-0 flex-1 py-0 text-xs"
              autoFocus
            />
          ) : (
            <button
              type="button"
              onClick={() => setNotesOpen(true)}
              className="text-[11px] text-muted-foreground/60 hover:text-muted-foreground"
            >
              + Notes
            </button>
          )}
          <ItemSaveIndicator status={saveStatus} />
        </div>
      </div>
    </div>
  )
}

interface ObservationsPanelProps {
  inspectionId: string
  section: string
  catalog: SectionCatalog
  numBedrooms?: number
  numBathrooms?: number
}

export function ObservationsPanel({
  inspectionId,
  section,
  catalog,
  numBedrooms = 0,
  numBathrooms = 0,
}: ObservationsPanelProps) {
  const {
    loading,
    metadata,
    observations,
    metaSaveStatus,
    itemSaveStatus,
    updateMetadata,
    updateObservation,
    rooms,
  } = useObservations({
    inspectionId,
    section,
    initialData: null,
    numBedrooms,
    numBathrooms,
  })

  const hasMetadata = Object.keys(catalog.metadata_fields).length > 0
  const hasItems = catalog.items.length > 0

  // Find the current observation for a given item + room combo
  const getObs = (item_key: string, room_index: number): ComponentObservation | undefined =>
    observations.find((o) => o.item_key === item_key && o.room_index === room_index)

  // Render condition items for a single room (or room_index=0 for non-room sections)
  function renderItems(room_index: number, room_label: string | null) {
    return catalog.items.map((item) => {
      const key = `${item.key}:${room_index}`
      const obs = getObs(item.key, room_index)
      const status = itemSaveStatus[key] ?? "idle"

      return (
        <ObservationItemRow
          key={key}
          itemKey={item.key}
          itemLabel={item.label}
          observation={obs}
          roomIndex={room_index}
          roomLabel={room_label}
          saveStatus={status}
          onConditionChange={(condition) => {
            void updateObservation(
              item.key,
              condition,
              obs?.observations ?? null,
              room_index,
              room_label,
            )
          }}
          onNotesBlur={(notes) => {
            const currentCondition = obs?.condition ?? null
            if (currentCondition !== null) {
              void updateObservation(
                item.key,
                currentCondition,
                notes || null,
                room_index,
                room_label,
              )
            }
          }}
        />
      )
    })
  }

  if (loading) {
    return (
      <div className="py-4 text-center text-xs text-muted-foreground">
        Loading observations…
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* ── Metadata fields ────────────────────────────────────────────── */}
      {hasMetadata && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Section Details
            </h3>
            {metaSaveStatus === "saving" && (
              <span className="text-[10px] text-muted-foreground">Saving…</span>
            )}
            {metaSaveStatus === "saved" && (
              <span className="text-[10px] text-emerald-600">Saved ✓</span>
            )}
            {metaSaveStatus === "error" && (
              <span className="text-[10px] text-destructive">⚠ Error</span>
            )}
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(catalog.metadata_fields).map(([key, field]) => (
              <MetadataField
                key={key}
                fieldKey={key}
                field={field}
                value={metadata[key] ?? null}
                onChange={(val) => updateMetadata(key, val)}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Condition items ────────────────────────────────────────────── */}
      {hasItems && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Component Conditions
          </h3>

          {catalog.is_room_based ? (
            /* Room-based: group by room. When no rooms configured, fall back to a
               single "General" room at index 0 so the inspector isn't blocked. */
            <div className="space-y-4">
              {(rooms === null || rooms.length === 0
                ? [{ room_index: 0, room_label: "General" }]
                : rooms
              ).map((room) => (
                <div key={room.room_index} className="space-y-1">
                  <p className="text-xs font-medium text-foreground">
                    {room.room_label}
                  </p>
                  <div className="rounded-md border border-border/60 bg-muted/10">
                    {renderItems(room.room_index, room.room_label)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Non-room: flat list at room_index=0 */
            <div className="rounded-md border border-border/60 bg-muted/10">
              {renderItems(0, null)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
