// apps/web/lib/findings.ts
import type { InspectionStatus } from "./inspections"

export const SECTIONS = [
  "FRONT",
  "EXTERIOR",
  "INSULATION",
  "PLUMBING",
  "STRUCTURAL",
  "ELECTRICAL",
  "ROOF",
  "KITCHEN",
  "INTERIOR",
  "AIR_CONDITIONING",
  "COMMENTS",
  "COST_ESTIMATION",
  "COUNTY_INFO",
  "DISCLOSURE",
] as const

export type Section = (typeof SECTIONS)[number]

export const SECTION_LABELS: Record<Section, string> = {
  FRONT: "Front",
  EXTERIOR: "Exterior",
  INSULATION: "Insulation",
  PLUMBING: "Plumbing",
  STRUCTURAL: "Structural",
  ELECTRICAL: "Electrical",
  ROOF: "Roof",
  KITCHEN: "Kitchen",
  INTERIOR: "Interior",
  AIR_CONDITIONING: "Air Conditioning",
  COMMENTS: "Comments",
  COST_ESTIMATION: "Cost Estimation",
  COUNTY_INFO: "County Info",
  DISCLOSURE: "Disclosure",
}

export const CONDITIONS = ["GOOD", "MARGINAL", "DEFECTIVE", "N_A"] as const

export type Condition = (typeof CONDITIONS)[number]

export const CONDITION_LABELS: Record<Condition, string> = {
  GOOD: "Good",
  MARGINAL: "Marginal",
  DEFECTIVE: "Defective",
  N_A: "N/A",
}

export type SaveStatus = "draft" | "saving" | "saved" | "error"

export interface Finding {
  id: string
  section: Section
  item: string
  condition?: Condition | null
  observations?: string | null
  estimated_cost?: number | null
  sort_order: number
  saveStatus: SaveStatus
}

export function isTempId(id: string) {
  return id.startsWith("temp-")
}

/**
 * How the `condition` field behaves for a given section.
 * - "required": condition selector is shown and must be filled to save.
 * - "optional": condition selector is shown but may be empty.
 * - "forbidden": condition selector is not rendered at all.
 */
export type ConditionRule = "required" | "optional" | "forbidden"

export interface SectionConfig {
  conditionRule: ConditionRule
  showEstimatedCost: boolean
  helper: string
}

export const SECTION_CONFIG: Record<Section, SectionConfig> = {
  FRONT: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Record front-of-property items and rate the condition of each.",
  },
  EXTERIOR: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Document exterior components and their condition.",
  },
  INSULATION: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Note insulation type, coverage, and condition.",
  },
  PLUMBING: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Record plumbing fixtures, supply, and drainage condition.",
  },
  STRUCTURAL: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Document structural elements and rate their condition.",
  },
  ELECTRICAL: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Record electrical service, panels, and devices condition.",
  },
  ROOF: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Document roof covering, flashing, and drainage condition.",
  },
  KITCHEN: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Record kitchen appliances, surfaces, and fixtures condition.",
  },
  INTERIOR: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Document interior rooms, finishes, and their condition.",
  },
  AIR_CONDITIONING: {
    conditionRule: "required",
    showEstimatedCost: false,
    helper: "Record HVAC equipment and rate the condition of each.",
  },
  COMMENTS: {
    conditionRule: "forbidden",
    showEstimatedCost: false,
    helper: "Free-form narrative notes. No condition rating required.",
  },
  COST_ESTIMATION: {
    conditionRule: "optional",
    showEstimatedCost: true,
    helper: "Line-item repair estimates. Condition is optional; enter a dollar amount.",
  },
  COUNTY_INFO: {
    conditionRule: "forbidden",
    showEstimatedCost: false,
    helper: "County and jurisdiction reference notes. No condition rating.",
  },
  DISCLOSURE: {
    conditionRule: "forbidden",
    showEstimatedCost: false,
    helper: "Disclosure statements and narrative notes. No condition rating.",
  },
}

export function getFindingErrors(finding: Finding): { item?: string; condition?: string } {
  const config = SECTION_CONFIG[finding.section]
  const errors: { item?: string; condition?: string } = {}

  if (!finding.item.trim()) {
    errors.item = "Item name is required."
  }

  if (config.conditionRule === "required" && !finding.condition) {
    errors.condition = "Condition is required for this section."
  }

  return errors
}

export function isFindingValid(finding: Finding): boolean {
  const errors = getFindingErrors(finding)
  return !errors.item && !errors.condition
}

// --- API response shape (snake_case from the backend) ---

export interface FindingResponse {
  id: string
  tenant_id: string
  inspection_id: string
  section: Section
  item: string
  condition: Condition | null
  observations: string | null
  estimated_cost: number | null
  sort_order: number
  created_at: string
  updated_at: string
}

export function mapFindingResponse(r: FindingResponse): Finding {
  return {
    id: r.id,
    section: r.section,
    item: r.item,
    condition: r.condition,
    observations: r.observations,
    estimated_cost: r.estimated_cost,
    sort_order: r.sort_order,
    saveStatus: "saved",
  }
}

// --- Mock data (kept for reference; no longer used by the live route) ---

export interface InspectionMeta {
  id: string
  address: string
  status: InspectionStatus
}

export const MOCK_INSPECTION: InspectionMeta = {
  id: "insp_001",
  address: "1420 Brickell Ave, Miami, FL 33131",
  status: "IN_FIELD",
}

let _counter = 0
const _id = () => `f_${Date.now().toString(36)}_${(_counter++).toString(36)}`

export const MOCK_FINDINGS: Finding[] = [
  {
    id: _id(),
    section: "ROOF",
    item: "Roof covering",
    condition: "DEFECTIVE",
    observations:
      "Multiple cracked and curling asphalt shingles on the south-facing slope. Granular loss observed.",
    estimated_cost: null,
    sort_order: 0,
    saveStatus: "saved",
  },
  {
    id: _id(),
    section: "ROOF",
    item: "Flashing",
    condition: "MARGINAL",
    observations: "Sealant at chimney flashing is deteriorating and should be monitored.",
    estimated_cost: null,
    sort_order: 1,
    saveStatus: "saved",
  },
  {
    id: _id(),
    section: "ROOF",
    item: "Gutters & downspouts",
    condition: "GOOD",
    observations: "",
    estimated_cost: null,
    sort_order: 2,
    saveStatus: "saved",
  },
  {
    id: _id(),
    section: "ELECTRICAL",
    item: "Main panel",
    condition: "GOOD",
    observations: "200A service, properly labeled. No double-tapped breakers observed.",
    estimated_cost: null,
    sort_order: 0,
    saveStatus: "saved",
  },
  {
    id: _id(),
    section: "COMMENTS",
    item: "General overview",
    observations:
      "Single-family residence, approx. 1998 construction. Property was occupied at time of inspection; some areas were obstructed by furniture and stored items.",
    estimated_cost: null,
    sort_order: 0,
    saveStatus: "saved",
  },
  {
    id: _id(),
    section: "COST_ESTIMATION",
    item: "Roof covering replacement (south slope)",
    condition: "DEFECTIVE",
    observations: "Estimate assumes full tear-off and re-shingle of the affected slope.",
    estimated_cost: 6800,
    sort_order: 0,
    saveStatus: "saved",
  },
]

export function newFinding(section: Section): Finding {
  return {
    id: `temp-${crypto.randomUUID()}`,
    section,
    item: "",
    condition: null,
    observations: "",
    estimated_cost: null,
    sort_order: 0,
    saveStatus: "draft",
  }
}
