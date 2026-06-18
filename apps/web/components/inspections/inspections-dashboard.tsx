"use client"

import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { Plus, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ALL_STATUSES,
  STATUS_LABELS,
  type Inspection,
  type NewInspectionPayload,
} from "@/lib/inspections"
import { InspectionsTable } from "./inspections-table"
import { InspectionsCards } from "./inspections-cards"
import { InspectionsEmptyState } from "./inspections-empty-state"
import { NewInspectionModal } from "./new-inspection-modal"

export function InspectionsDashboard({
  initialInspections,
}: {
  initialInspections: Inspection[]
}) {
  const router = useRouter()
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("ALL")
  const [modalOpen, setModalOpen] = useState(false)

  const filtered = useMemo(() => {
    return initialInspections.filter((inspection) => {
      const matchesSearch = inspection.property_address
        .toLowerCase()
        .includes(search.trim().toLowerCase())
      const matchesStatus =
        statusFilter === "ALL" || inspection.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [initialInspections, search, statusFilter])

  const hasNoInspections = initialInspections.length === 0
  const hasNoResults = initialInspections.length > 0 && filtered.length === 0

  async function handleCreateInspection(payload: NewInspectionPayload) {
    const res = await fetch("/api/inspections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (res.status === 401) {
      router.push("/login")
      return
    }
    if (!res.ok) {
      const data = await res.json().catch(() => null)
      throw new Error(
        (data?.detail as string | undefined) ??
          (data?.error as string | undefined) ??
          "Failed to create inspection.",
      )
    }
    const inspection = (await res.json()) as { id: string }
    router.push(`/inspections/${inspection.id}`)
  }

  return (
    <>
      <NewInspectionModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onSubmit={handleCreateInspection}
      />

      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Inspections
            </h1>
            <p className="text-sm text-muted-foreground">
              Manage scheduled, in-progress, and delivered inspection reports.
            </p>
          </div>
          <Button className="shrink-0" onClick={() => setModalOpen(true)}>
            <Plus className="size-4" aria-hidden="true" />
            New Inspection
          </Button>
        </div>

        {!hasNoInspections && (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden="true"
              />
              <Input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by address..."
                className="bg-card pl-9"
                aria-label="Search inspections by address"
              />
            </div>
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "ALL")}>
              <SelectTrigger className="w-full bg-card sm:w-48" aria-label="Filter by status">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All statuses</SelectItem>
                {ALL_STATUSES.map((status) => (
                  <SelectItem key={status} value={status}>
                    {STATUS_LABELS[status]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {hasNoInspections && (
          <InspectionsEmptyState onNewInspection={() => setModalOpen(true)} />
        )}

        {hasNoResults && (
          <div className="rounded-lg border border-dashed border-border bg-card px-6 py-16 text-center">
            <p className="text-sm font-medium text-foreground">
              No inspections match your filters
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Try adjusting your search or status filter.
            </p>
          </div>
        )}

        {filtered.length > 0 && (
          <>
            <InspectionsTable inspections={filtered} />
            <InspectionsCards inspections={filtered} />
          </>
        )}
      </div>
    </>
  )
}
