"use client"

import { useCallback, useMemo, useState } from "react"
import type { InspectionDetailData } from "@/lib/inspection-detail"

export type SaveStatus = "idle" | "saving" | "saved" | "error"

// All editable fields sent to PUT /api/inspections/{id}.
// id, status, tenant_id, and inspector_id are read-only from this form.
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

/**
 * Holds the entire inspection detail form in a single object.
 * Initial data comes from the server GET; save() sends PUT via the route handler.
 */
export function useInspectionDetail(initial: InspectionDetailData) {
  const [initialData, setInitialData] = useState<InspectionDetailData>(initial)
  const [data, setData] = useState<InspectionDetailData>(initial)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle")

  const setField = useCallback(
    <K extends keyof InspectionDetailData>(key: K, value: InspectionDetailData[K]) => {
      setData((prev) => ({ ...prev, [key]: value }))
      // Clear error/saved indicator as soon as the user makes a new edit.
      setSaveStatus((s) => (s === "saving" ? s : "idle"))
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

  /** Advance the baseline without a network call (used externally if needed). */
  const commit = useCallback(() => {
    setInitialData(data)
  }, [data])

  /**
   * PUT /api/inspections/{id} via the Next.js route handler (which injects the
   * httpOnly cookie server-side). Returns { ok, status } so the caller can handle 401.
   */
  const save = useCallback(async (): Promise<{ ok: boolean; status: number }> => {
    setSaveStatus("saving")
    try {
      const res = await fetch(`/api/inspections/${data.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPutBody(data)),
      })
      if (res.ok) {
        setInitialData(data) // saved values become the new dirty baseline
        setSaveStatus("saved")
        return { ok: true, status: res.status }
      }
      // Don't leave the button in "saving" state on 401 — caller will redirect.
      setSaveStatus(res.status === 401 ? "idle" : "error")
      return { ok: false, status: res.status }
    } catch {
      setSaveStatus("error")
      return { ok: false, status: 0 }
    }
  }, [data])

  return { data, setField, isDirty, saveStatus, reset, commit, save }
}

export type InspectionDetailFormApi = ReturnType<typeof useInspectionDetail>
