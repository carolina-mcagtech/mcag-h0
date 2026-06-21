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
