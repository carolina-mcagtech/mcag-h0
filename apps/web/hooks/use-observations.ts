"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type {
  ComponentCondition,
  ComponentObservation,
  SectionObservationsResponse,
} from "@/lib/observations"

type SaveStatusType = "idle" | "saving" | "saved" | "error"

interface Room {
  room_index: number
  room_label: string
}

interface UseObservationsProps {
  inspectionId: string
  section: string
  initialData: SectionObservationsResponse | null
  numBedrooms?: number
  numBathrooms?: number
}

export function useObservations({
  inspectionId,
  section,
  initialData,
  numBedrooms = 0,
  numBathrooms = 0,
}: UseObservationsProps) {
  const [loading, setLoading] = useState(initialData === null)
  const [metadata, setMetadata] = useState<Record<string, unknown>>(
    initialData?.metadata ?? {},
  )
  const [observations, setObservations] = useState<ComponentObservation[]>(
    initialData?.observations ?? [],
  )
  const [metaSaveStatus, setMetaSaveStatus] = useState<SaveStatusType>("idle")
  const [itemSaveStatus, setItemSaveStatus] = useState<
    Record<string, SaveStatusType>
  >({})

  // Always-current ref for metadata (avoids stale closure in debounce timer)
  const metadataRef = useRef<Record<string, unknown>>(metadata)
  const metaTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    metadataRef.current = metadata
  }, [metadata])

  // Fetch section data on mount
  useEffect(() => {
    if (initialData !== null) return

    setLoading(true)
    fetch(`/api/inspections/${inspectionId}/observations/${section}`)
      .then((res) => (res.ok ? (res.json() as Promise<SectionObservationsResponse>) : null))
      .then((data) => {
        if (data) {
          setMetadata(data.metadata)
          metadataRef.current = data.metadata
          setObservations(data.observations)
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [inspectionId, section, initialData])

  // Clean up debounce timer on unmount
  useEffect(() => {
    return () => {
      if (metaTimerRef.current) clearTimeout(metaTimerRef.current)
    }
  }, [])

  const updateMetadata = useCallback(
    (field: string, value: unknown) => {
      setMetadata((prev) => {
        const next = { ...prev, [field]: value }
        metadataRef.current = next
        return next
      })
      setMetaSaveStatus("saving")

      if (metaTimerRef.current) clearTimeout(metaTimerRef.current)
      metaTimerRef.current = setTimeout(async () => {
        try {
          const res = await fetch(
            `/api/inspections/${inspectionId}/observations/${section}/metadata`,
            {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ section, data: metadataRef.current }),
            },
          )
          if (res.ok) {
            setMetaSaveStatus("saved")
            setTimeout(() => setMetaSaveStatus("idle"), 2500)
          } else {
            setMetaSaveStatus("error")
          }
        } catch {
          setMetaSaveStatus("error")
        }
      }, 800)
    },
    [inspectionId, section],
  )

  const updateObservation = useCallback(
    async (
      item_key: string,
      condition: ComponentCondition | null,
      obsText: string | null,
      room_index: number,
      room_label: string | null,
    ) => {
      // Condition is required by the backend; skip if unset
      if (condition === null) return

      const key = `${item_key}:${room_index}`
      setItemSaveStatus((prev) => ({ ...prev, [key]: "saving" }))

      // Optimistic update
      setObservations((prev) => {
        const idx = prev.findIndex(
          (o) => o.item_key === item_key && o.room_index === room_index,
        )
        if (idx >= 0) {
          return prev.map((o) =>
            o.item_key === item_key && o.room_index === room_index
              ? { ...o, condition, observations: obsText, room_label }
              : o,
          )
        }
        return prev
      })

      try {
        const res = await fetch(
          `/api/inspections/${inspectionId}/observations/${section}/items/${item_key}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              section,
              item_key,
              condition,
              observations: obsText,
              room_index,
              room_label,
            }),
          },
        )

        if (res.ok) {
          const updated = (await res.json()) as ComponentObservation
          setObservations((prev) => {
            const idx = prev.findIndex(
              (o) => o.item_key === item_key && o.room_index === room_index,
            )
            if (idx >= 0) {
              return prev.map((o) =>
                o.item_key === item_key && o.room_index === room_index ? updated : o,
              )
            }
            return [...prev, updated]
          })
          setItemSaveStatus((prev) => ({ ...prev, [key]: "saved" }))
          setTimeout(
            () => setItemSaveStatus((prev) => ({ ...prev, [key]: "idle" })),
            2500,
          )
        } else {
          setItemSaveStatus((prev) => ({ ...prev, [key]: "error" }))
        }
      } catch {
        setItemSaveStatus((prev) => ({ ...prev, [key]: "error" }))
      }
    },
    [inspectionId, section],
  )

  // Room list for room-based sections
  const rooms = useMemo((): Room[] | null => {
    if (section === "BEDROOMS" && numBedrooms > 0) {
      return Array.from({ length: numBedrooms }, (_, i) => ({
        room_index: i + 1,
        room_label: i === 0 ? "Master Bedroom" : `Bedroom ${i + 1}`,
      }))
    }
    if (section === "BATHROOMS" && numBathrooms > 0) {
      return Array.from({ length: numBathrooms }, (_, i) => ({
        room_index: i + 1,
        room_label: i === 0 ? "Master Bathroom" : `Bathroom ${i + 1}`,
      }))
    }
    return null
  }, [section, numBedrooms, numBathrooms])

  return {
    loading,
    metadata,
    observations,
    metaSaveStatus,
    itemSaveStatus,
    updateMetadata,
    updateObservation,
    rooms,
  }
}
