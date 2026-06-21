// lib/observations.ts

export type ComponentCondition = "GOOD" | "MARGINAL" | "DEFECTIVE" | "N_A"

export interface CatalogMetadataField {
  type: "text" | "select" | "multiselect" | "number"
  label: string
  options?: string[]
}

export interface CatalogItem {
  key: string
  label: string
  sort_order: number
}

export interface SectionCatalog {
  label: string
  metadata_fields: Record<string, CatalogMetadataField>
  items: CatalogItem[]
  is_room_based?: boolean
  room_type?: string
}

export interface ComponentObservation {
  id: string
  inspection_id: string
  section: string
  item_key: string
  item_label: string
  condition: ComponentCondition
  observations: string | null
  room_type: string | null
  room_index: number
  room_label: string | null
  sort_order: number
}

export interface SectionObservationsResponse {
  section: string
  label: string
  catalog: SectionCatalog
  metadata: Record<string, unknown>
  observations: ComponentObservation[]
}

export const CONDITION_LABELS: Record<ComponentCondition, string> = {
  GOOD: "Good",
  MARGINAL: "Marginal",
  DEFECTIVE: "Defective",
  N_A: "N/A",
}

export const CONDITIONS: ComponentCondition[] = ["GOOD", "MARGINAL", "DEFECTIVE", "N_A"]

export const FINDINGS_TO_CATALOG_SECTION: Record<string, string | string[] | null> = {
  INSULATION: "INSULATION_VENTILATION",
  KITCHEN: ["INTERIOR_KITCHEN_DINING", "INTERIOR_APPLIANCES"],
  AIR_CONDITIONING: "AIR_CONDITIONING",
  STRUCTURAL: "STRUCTURAL",
  EXTERIOR: "EXTERIOR",
  ROOF: "ROOF",
  ELECTRICAL: "ELECTRICAL",
  PLUMBING: "PLUMBING",
  FRONT: null,
  INTERIOR: null,
  COMMENTS: null,
  COST_ESTIMATION: null,
  COUNTY_INFO: null,
  DISCLOSURE: null,
  BEDROOMS: "BEDROOMS",
  BATHROOMS: "BATHROOMS",
}
