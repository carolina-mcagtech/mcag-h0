"use client"

import { useRouter } from "next/navigation"
import {
  CalendarClockIcon,
  HomeIcon,
  UsersIcon,
  HashIcon,
  HardHatIcon,
  FlameIcon,
  ZapIcon,
  WindIcon,
  StickyNoteIcon,
  ThermometerIcon,
} from "lucide-react"

import {
  type InspectionDetailData,
  type FindingsSummary as FindingsSummaryData,
  PAYMENT_TIMING_OPTIONS,
} from "@/lib/inspection-detail"
import { useInspectionDetail } from "@/hooks/use-inspection-detail"

import { AddressAutocomplete } from "@/components/ui/address-autocomplete"
import { InspectionHeader } from "./inspection-header"
import { FindingsSummary } from "./findings-summary"
import { SectionCard } from "./section-card"
import { InspectionTypesField } from "./inspection-types-field"
import { Field, FieldLabel } from "@/components/ui/field"
import {
  TextField,
  NumberField,
  CurrencyField,
  SelectField,
  TextareaField,
  SwitchField,
} from "./form-fields"

export function InspectionDetail({
  inspection,
  findings,
}: {
  inspection: InspectionDetailData
  findings: FindingsSummaryData
}) {
  const router = useRouter()
  const { data, setField, saveStatus, transition, transitionStatus, transitionError } = useInspectionDetail(inspection)

  const readOnly = data.status === "DELIVERED" || data.status === "PUBLISHED"

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <InspectionHeader
        address={data.property_address}
        status={data.status}
        inspectionId={data.id}
        saveStatus={saveStatus}
        transitionStatus={transitionStatus}
        transitionError={transitionError}
        onBack={() => router.push("/inspections")}
        onEditFindings={() => router.push(`/inspections/${data.id}/findings`)}
        onTransition={transition}
      />

    <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-6 md:px-6">
      {readOnly && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          This inspection has been delivered and is read-only.
        </div>
      )}
      <FindingsSummary data={findings} />

      <div className="flex flex-col gap-6">
        {/* 1. Schedule & Basics */}
        <SectionCard
          icon={CalendarClockIcon}
          title="Schedule & Basics"
          description="Appointment, services, and payment."
        >
          <div className="sm:col-span-2">
            <Field>
              <FieldLabel>Property Address</FieldLabel>
              <AddressAutocomplete
                value={data.property_address ?? ""}
                onChange={(v) => setField("property_address", v)}
                placeholder="123 Main St, Miami, FL 33101"
                disabled={readOnly}
                className="w-full max-w-full"
              />
            </Field>
          </div>
          <TextField
            label="Scheduled At"
            type="datetime-local"
            value={data.scheduled_at}
            onChange={(v) => setField("scheduled_at", v)}
            disabled={readOnly}
          />
          <CurrencyField
            label="Total Fee"
            value={data.total_fee}
            onChange={(v) => setField("total_fee", v)}
            disabled={readOnly}
          />
          <div className="sm:col-span-2">
            <InspectionTypesField
              value={data.inspection_types}
              onChange={(v) => setField("inspection_types", v)}
              disabled={readOnly}
            />
          </div>
          <SelectField
            label="Payment Timing"
            value={data.payment_timing}
            onChange={(v) =>
              setField("payment_timing", v as InspectionDetailData["payment_timing"])
            }
            options={PAYMENT_TIMING_OPTIONS}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 2. Property */}
        <SectionCard
          icon={HomeIcon}
          title="Property"
          description="Building details and access."
        >
          <NumberField
            label="Year Built"
            value={data.year_built}
            onChange={(v) => setField("year_built", v)}
            disabled={readOnly}
          />
          <NumberField
            label="Adjusted Sq Ft"
            value={data.adj_sqft}
            onChange={(v) => setField("adj_sqft", v)}
            disabled={readOnly}
          />
          <TextField
            label="Gate Code"
            value={data.gate_code}
            onChange={(v) => setField("gate_code", v)}
            disabled={readOnly}
          />
          <TextField
            label="Lockbox"
            value={data.lockbox}
            onChange={(v) => setField("lockbox", v)}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 3. Contacts */}
        <SectionCard
          icon={UsersIcon}
          title="Contacts"
          description="Realtor, owner/buyer, and listing agent."
        >
          <TextField
            label="Realtor Name"
            value={data.realtor_name}
            onChange={(v) => setField("realtor_name", v)}
            disabled={readOnly}
          />
          <TextField
            label="Realtor Cell"
            type="tel"
            value={data.realtor_cell}
            onChange={(v) => setField("realtor_cell", v)}
            disabled={readOnly}
          />
          <TextField
            label="Owner / Buyer Name"
            value={data.owner_buyer_name}
            onChange={(v) => setField("owner_buyer_name", v)}
            disabled={readOnly}
          />
          <TextField
            label="Owner / Buyer Cell"
            type="tel"
            value={data.owner_buyer_cell}
            onChange={(v) => setField("owner_buyer_cell", v)}
            disabled={readOnly}
          />
          <TextField
            label="Owner / Buyer Email"
            type="email"
            value={data.owner_buyer_email}
            onChange={(v) => setField("owner_buyer_email", v)}
            disabled={readOnly}
          />
          <TextField
            label="Listing Agent Name"
            value={data.listing_agent_name}
            onChange={(v) => setField("listing_agent_name", v)}
            disabled={readOnly}
          />
          <TextField
            label="Listing Agent Cell"
            type="tel"
            value={data.listing_agent_cell}
            onChange={(v) => setField("listing_agent_cell", v)}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 4. Report Numbers */}
        <SectionCard
          icon={HashIcon}
          title="Report Numbers"
          description="Reference numbers for generated reports."
        >
          <TextField
            label="Full Report Number"
            value={data.full_report_number}
            onChange={(v) => setField("full_report_number", v)}
            disabled={readOnly}
          />
          <TextField
            label="Insurance Report Number"
            value={data.insurance_report_number}
            onChange={(v) => setField("insurance_report_number", v)}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 5. Roof */}
        <SectionCard
          icon={HardHatIcon}
          title="Roof"
          description="Roof permit, age, and construction."
        >
          <TextField
            label="Roof Permit Number"
            value={data.roof_permit_number}
            onChange={(v) => setField("roof_permit_number", v)}
            disabled={readOnly}
          />
          <TextField
            label="Roof Year"
            type="text"
            inputMode="numeric"
            pattern="[0-9]{4}"
            placeholder="e.g. 2019"
            value={data.roof_date}
            onChange={(v) => setField("roof_date", v)}
            disabled={readOnly}
          />
          <TextField
            label="Roof Style"
            value={data.roof_style}
            onChange={(v) => setField("roof_style", v)}
            disabled={readOnly}
          />
          <TextField
            label="Roof Type"
            value={data.roof_type}
            onChange={(v) => setField("roof_type", v)}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 6. Water Heater */}
        <SectionCard
          icon={FlameIcon}
          title="Water Heater"
          description="Type, location, and capacity."
          columns={3}
        >
          <TextField
            label="Type"
            value={data.water_heater_type}
            onChange={(v) => setField("water_heater_type", v)}
            disabled={readOnly}
          />
          <TextField
            label="Location"
            value={data.water_heater_location}
            onChange={(v) => setField("water_heater_location", v)}
            disabled={readOnly}
          />
          <TextField
            label="Capacity"
            value={data.water_heater_capacity}
            onChange={(v) => setField("water_heater_capacity", v)}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 7. Electrical */}
        <SectionCard
          icon={ZapIcon}
          title="Electrical"
          description="Panel brand, amperage, and location."
          columns={3}
        >
          <TextField
            label="Brand"
            value={data.electrical_brand}
            onChange={(v) => setField("electrical_brand", v)}
            disabled={readOnly}
          />
          <NumberField
            label="Amps"
            value={data.electrical_amps}
            onChange={(v) => setField("electrical_amps", v)}
            disabled={readOnly}
          />
          <TextField
            label="Location"
            value={data.electrical_location}
            onChange={(v) => setField("electrical_location", v)}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 8. HVAC */}
        <SectionCard
          icon={ThermometerIcon}
          title="HVAC"
          description="System brand, age, and model."
        >
          <TextField
            label="Brand"
            value={data.hvac_brand}
            onChange={(v) => setField("hvac_brand", v)}
            disabled={readOnly}
          />
          <NumberField
            label="Age (years)"
            value={data.hvac_age}
            onChange={(v) => setField("hvac_age", v)}
            disabled={readOnly}
          />
          <TextField
            label="Model"
            value={data.hvac_model}
            onChange={(v) => setField("hvac_model", v)}
            disabled={readOnly}
          />
          <TextField
            label="Series"
            value={data.hvac_series}
            onChange={(v) => setField("hvac_series", v)}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 9. Wind Mitigation */}
        <SectionCard
          icon={WindIcon}
          title="Wind Mitigation"
          description="Opening protection status."
        >
          <SwitchField
            label="Doors Protected"
            description="Exterior doors have rated protection."
            checked={data.wind_mit_doors_protected}
            onChange={(v) => setField("wind_mit_doors_protected", v)}
            disabled={readOnly}
          />
          <SwitchField
            label="Windows Protected"
            description="Windows have rated protection."
            checked={data.wind_mit_windows_protected}
            onChange={(v) => setField("wind_mit_windows_protected", v)}
            disabled={readOnly}
          />
        </SectionCard>

        {/* 10. Notes */}
        <SectionCard
          icon={StickyNoteIcon}
          title="Notes"
          description="Additional context for this inspection."
          columns={1}
        >
          <TextareaField
            label="Additional Notes"
            value={data.additional_notes}
            onChange={(v) => setField("additional_notes", v)}
            placeholder="Add any additional notes…"
            disabled={readOnly}
          />
        </SectionCard>
      </div>
    </main>
    </div>
  )
}
