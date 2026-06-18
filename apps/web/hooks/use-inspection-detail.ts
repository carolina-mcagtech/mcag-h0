"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import type { InspectionDetailData } from "@/lib/inspection-detail"

export type SaveStatus = "idle" | "saving" | "saved" | "error"

const DEBOUNCE_MS = 800
const SAVED_RESET_MS = 2500

function buildPutBody(d: InspectionDetailData) {
  return {
    scheduled_at: d.scheduled_at,
    property_address: d.property_address,
    inspection_types: d.inspection_types,
    total_fee: d.total_fee,
    payment_timing: d.payment_timing,
    year_built: d.year_built,
    adj_sqft: d.adj_sqft,
    gate_code: d.gate_code,
    lockbox: d.lockbox,
    realtor_name: d.realtor_name,
    realtor_cell: d.realtor_cell,
    owner_buyer_name: d.owner_buyer_name,
    owner_buyer_cell: d.owner_buyer_cell,
    owner_buyer_email: d.owner_buyer_email,
    listing_agent_name: d.listing_agent_name,
    listing_agent_cell: d.listing_agent_cell,
    additional_notes: d.additional_notes,
    full_report_number: d.full_report_number,
    insurance_report_number: d.insurance_report_number,
    roof_permit_number: d.roof_permit_number,
    roof_date: d.roof_date,
    roof_style: d.roof_style,
    roof_type: d.roof_type,
    water_heater_type: d.water_heater_type,
    water_heater_location: d.water_heater_location,
    water_heater_capacity: d.water_heater_capacity,
    electrical_brand: d.electrical_brand,
    electrical_amps: d.electrical_amps,
    electrical_location: d.electrical_location,
    hvac_brand: d.hvac_brand,
    hvac_age: d.hvac_age,
    hvac_model: d.hvac_model,
    hvac_series: d.hvac_series,
    wind_mit_doors_protected: d.wind_mit_doors_protected,
    wind_mit_windows_protected: d.wind_mit_windows_protected,
  }
}

// Strip timezone suffix from an ISO timestamp so datetime-local inputs are happy.
// "2026-06-20T08:00:00Z" → "2026-06-20T08:00"
function normalizeInitial(d: InspectionDetailData): InspectionDetailData {
  return {
    ...d,
    scheduled_at: d.scheduled_at
      ? d.scheduled_at.replace(/:\d{2}(\.\d+)?Z?$/, "").slice(0, 16)
      : null,
  }
}

export function useInspectionDetail(initial: InspectionDetailData) {
  const router = useRouter()
  const normalized = normalizeInitial(initial)
  const [data, setData] = useState<InspectionDetailData>(normalized)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle")

  // Always-current refs so the debounce callback never closes over stale values.
  const dataRef = useRef<InspectionDetailData>(normalized)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const savedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Ref to the latest autosave closure — same pattern as persistFindingRef in use-findings.ts.
  const autosaveRef = useRef<() => Promise<void>>(async () => {})

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      if (savedTimerRef.current) clearTimeout(savedTimerRef.current)
    }
  }, [])

  const autosave = useCallback(async () => {
    const snapshot = dataRef.current
    setSaveStatus("saving")
    try {
      const res = await fetch(`/api/inspections/${snapshot.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPutBody(snapshot)),
      })
      if (res.status === 401) {
        router.push("/login")
        return
      }
      if (res.ok) {
        setSaveStatus("saved")
        if (savedTimerRef.current) clearTimeout(savedTimerRef.current)
        savedTimerRef.current = setTimeout(() => setSaveStatus("idle"), SAVED_RESET_MS)
      } else {
        setSaveStatus("error")
      }
    } catch {
      setSaveStatus("error")
    }
  }, [router])

  // Keep the ref pointing at the latest closure so the timer always calls
  // the freshest autosave regardless of when useCallback was last re-created.
  autosaveRef.current = autosave

  // Empty deps — scheduleAutosave is truly stable and reads data via dataRef,
  // autosave via autosaveRef. No closure over potentially-stale values.
  const scheduleAutosave = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      timerRef.current = null
      autosaveRef.current()
    }, DEBOUNCE_MS)
  }, [])

  const setField = useCallback(
    <K extends keyof InspectionDetailData>(key: K, value: InspectionDetailData[K]) => {
      setData((prev) => {
        const next = { ...prev, [key]: value }
        dataRef.current = next
        return next
      })
      scheduleAutosave()
    },
    [scheduleAutosave],
  )

  return { data, setField, saveStatus }
}

export type InspectionDetailFormApi = ReturnType<typeof useInspectionDetail>
