"use client"

import { useCallback, useMemo, useState } from "react"
import type { InspectionDetailData } from "@/lib/inspection-detail"

/**
 * Holds the entire inspection detail form in a single object.
 * Swap `initial` for a real GET response to go live; call PUT with `getPayload()`.
 */
export function useInspectionDetail(initial: InspectionDetailData) {
  const [initialData, setInitialData] = useState<InspectionDetailData>(initial)
  const [data, setData] = useState<InspectionDetailData>(initial)

  const setField = useCallback(
    <K extends keyof InspectionDetailData>(key: K, value: InspectionDetailData[K]) => {
      setData((prev) => ({ ...prev, [key]: value }))
    },
    [],
  )

  const isDirty = useMemo(
    () => JSON.stringify(data) !== JSON.stringify(initialData),
    [data, initialData],
  )

  const reset = useCallback(() => {
    setData(initialData)
  }, [initialData])

  /** Call after a successful PUT to make the current values the new baseline. */
  const commit = useCallback(() => {
    setInitialData(data)
  }, [data])

  const getPayload = useCallback(() => data, [data])

  return { data, setField, isDirty, reset, commit, getPayload }
}

export type InspectionDetailFormApi = ReturnType<typeof useInspectionDetail>
