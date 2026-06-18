// apps/web/lib/inspection-detail.ts
// Types and constants for the Inspection Detail page.
// Mirrors the InspectionUpdate schema from the API (all editable fields optional).

export type InspectionStatus =
  | "DRAFT"
  | "IN_FIELD"
  | "PENDING_REVIEW"
  | "PUBLISHED"
  | "DELIVERED"

export const INSPECTION_STATUS_META: Record<
  InspectionStatus,
  { label: string; className: string }
> = {
  DRAFT: {
    label: "Draft",
    className: "bg-slate-100 text-slate-700 border-slate-200",
  },
  IN_FIELD: {
    label: "In Field",
    className: "bg-blue-100 text-blue-700 border-blue-200",
  },
  PENDING_REVIEW: {
    label: "Pending Review",
    className: "bg-amber-100 text-amber-800 border-amber-200",
  },
  PUBLISHED: {
    label: "Published",
    className: "bg-green-100 text-green-700 border-green-200",
  },
  DELIVERED: {
    label: "Delivered",
    className: "bg-teal-100 text-teal-700 border-teal-200",
  },
}

// Matches InspectionTypeEnum from the API.
export type InspectionTypeValue =
  | "FULL_INSPECTION"
  | "WIND_MITIGATION"
  | "FOUR_POINT"
  | "MOLD_INSPECTION"
  | "TERMITES"
  | "ROOF_CERTIFICATION"
  | "OPENING_PROTECTION"
  | "SEWER_INSPECTION"
  | "LEAD_PAINT_INSPECTION"
  | "WATER_QUALITY_TEST"

export const INSPECTION_TYPE_OPTIONS: {
  value: InspectionTypeValue
  label: string
}[] = [
  { value: "FULL_INSPECTION", label: "Full Inspection" },
  { value: "WIND_MITIGATION", label: "Wind Mitigation" },
  { value: "FOUR_POINT", label: "4-Point" },
  { value: "MOLD_INSPECTION", label: "Mold Inspection" },
  { value: "TERMITES", label: "Termites" },
  { value: "ROOF_CERTIFICATION", label: "Roof Certification" },
  { value: "OPENING_PROTECTION", label: "Opening Protection" },
  { value: "SEWER_INSPECTION", label: "Sewer Inspection" },
  { value: "LEAD_PAINT_INSPECTION", label: "Lead Paint Inspection" },
  { value: "WATER_QUALITY_TEST", label: "Water Quality Test" },
]

// Matches PaymentTimingEnum from the API.
export type PaymentTiming =
  | "AT_PROPERTY"
  | "AT_DELIVERY"
  | "AFTER_DELIVERY"

export const PAYMENT_TIMING_OPTIONS: {
  value: PaymentTiming
  label: string
}[] = [
  { value: "AT_PROPERTY", label: "At Property" },
  { value: "AT_DELIVERY", label: "At Delivery" },
  { value: "AFTER_DELIVERY", label: "After Delivery" },
]

// Full editable shape — mirrors InspectionUpdate from the API.
export interface InspectionDetailData {
  id: string
  property_address: string
  status: InspectionStatus

  // Identity
  inspector_id: string | null

  // Schedule & Basics
  scheduled_at: string | null
  inspection_types: InspectionTypeValue[]
  total_fee: number | null
  payment_timing: PaymentTiming | null

  // Property
  year_built: number | null
  adj_sqft: number | null
  gate_code: string | null
  lockbox: string | null

  // Contacts
  realtor_name: string | null
  realtor_cell: string | null
  owner_buyer_name: string | null
  owner_buyer_cell: string | null
  owner_buyer_email: string | null
  listing_agent_name: string | null
  listing_agent_cell: string | null

  // Report Numbers
  full_report_number: string | null
  insurance_report_number: string | null

  // Roof
  roof_permit_number: string | null
  roof_date: string | null
  roof_style: string | null
  roof_type: string | null

  // Water Heater
  water_heater_type: string | null
  water_heater_location: string | null
  water_heater_capacity: string | null

  // Electrical
  electrical_brand: string | null
  electrical_amps: number | null
  electrical_location: string | null

  // HVAC
  hvac_brand: string | null
  hvac_age: number | null
  hvac_model: string | null
  hvac_series: string | null

  // Wind Mitigation
  wind_mit_doors_protected: boolean
  wind_mit_windows_protected: boolean

  // Notes
  additional_notes: string | null
}

// Findings summary per section: Record<sectionKey, {total, defective}>
// Does NOT include appliances/rooms (handled separately later).
export type FindingsSummary = Record<
  string,
  { total: number; defective: number }
>

export const MOCK_INSPECTION: InspectionDetailData = {
  id: "insp_001",
  property_address: "1420 Brickell Ave, Miami, FL 33131",
  status: "IN_FIELD",

  inspector_id: null,

  scheduled_at: "2026-06-24T09:30",
  inspection_types: ["FULL_INSPECTION", "WIND_MITIGATION", "FOUR_POINT"],
  total_fee: 575,
  payment_timing: "AT_PROPERTY",

  year_built: 1998,
  adj_sqft: 2640,
  gate_code: "4821",
  lockbox: "Front door, code 0517",

  realtor_name: "Carmen Diaz",
  realtor_cell: "(305) 555-0142",
  owner_buyer_name: "Jonathan Reyes",
  owner_buyer_cell: "(786) 555-0199",
  owner_buyer_email: "j.reyes@example.com",
  listing_agent_name: "Marcus Webb",
  listing_agent_cell: "(305) 555-0177",

  full_report_number: "FR-2026-1042",
  insurance_report_number: "INS-2026-0883",

  roof_permit_number: "RP-118204",
  roof_date: "2014-08-12",
  roof_style: "Hip",
  roof_type: "Concrete Tile",

  water_heater_type: "Electric",
  water_heater_location: "Garage",
  water_heater_capacity: "50 gal",

  electrical_brand: "Square D",
  electrical_amps: 200,
  electrical_location: "Exterior west wall",

  hvac_brand: "Carrier",
  hvac_age: 7,
  hvac_model: "24ACC636",
  hvac_series: "Comfort 16",

  wind_mit_doors_protected: true,
  wind_mit_windows_protected: true,

  additional_notes:
    "Pool equipment inspected separately. Seller reports water heater replaced 2021. Verify permit on roof recover.",
}

export const MOCK_FINDINGS_SUMMARY: FindingsSummary = {
  ROOF: { total: 3, defective: 1 },
  ELECTRICAL: { total: 2, defective: 0 },
  PLUMBING: { total: 4, defective: 2 },
  HVAC: { total: 2, defective: 0 },
  EXTERIOR: { total: 1, defective: 0 },
}

export function formatSectionName(name: string): string {
  return name
    .toLowerCase()
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ")
}
