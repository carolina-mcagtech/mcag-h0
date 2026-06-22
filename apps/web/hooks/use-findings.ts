"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import {
  type Finding,
  type InspectionMeta,
  type SaveStatus,
  type Section,
  SECTION_CONFIG,
  getFindingErrors,
  isFindingValid,
  isTempId,
  newFinding,
} from "@/lib/findings"

const DEBOUNCE_MS = 800

// ------------------------------------------------------------
// Body builders — module-level (no hook state needed)
// ------------------------------------------------------------

type CreateBody = Record<string, unknown>
type UpdateBody = Record<string, unknown>

function buildCreateBody(f: Finding): CreateBody {
  const config = SECTION_CONFIG[f.section]
  const body: CreateBody = { section: f.section, item: f.item, sort_order: f.sort_order }
  if (f.observations) body.observations = f.observations
  if (config.conditionRule !== "forbidden" && f.condition) body.condition = f.condition
  if (config.showEstimatedCost && f.estimated_cost != null) body.estimated_cost = f.estimated_cost
  return body
}

function buildUpdateBody(f: Finding): UpdateBody {
  const config = SECTION_CONFIG[f.section]
  const body: UpdateBody = { item: f.item, sort_order: f.sort_order }
  body.observations = f.observations ?? null
  if (config.conditionRule !== "forbidden") body.condition = f.condition ?? null
  if (config.showEstimatedCost) body.estimated_cost = f.estimated_cost ?? null
  return body
}

// ------------------------------------------------------------
// Hook
// ------------------------------------------------------------

export type GlobalSaveStatus = "idle" | "saving" | "pending" | "error" | "all-saved"

export function useFindings(initialFindings: Finding[], inspection: InspectionMeta) {
  const router = useRouter()

  // findings state + a ref that is always in sync with it
  const [findings, setFindingsState] = useState<Finding[]>(initialFindings)
  const findingsRef = useRef<Finding[]>(initialFindings)
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  // ref to break circular dep between scheduleSave ↔ persistFinding
  const persistFindingRef = useRef<((f: Finding) => Promise<void>) | null>(null)

  // True after the first successful network save. Drives "All changes saved"
  // visibility. Using state (not ref) so resetting it triggers a re-render
  // and globalSaveStatus falls back to "idle".
  const [hasSavedOnce, setHasSavedOnce] = useState(false)

  // setFindings wrapper that keeps the ref in sync synchronously
  const setFindings = useCallback((updater: (prev: Finding[]) => Finding[]) => {
    setFindingsState((prev) => {
      const next = updater(prev)
      findingsRef.current = next
      return next
    })
  }, [])

  // Cancel all timers on unmount
  useEffect(() => {
    return () => {
      timers.current.forEach((t) => clearTimeout(t))
    }
  }, [])

  // Schedule a debounced save for the finding with the given id.
  // Reads current state from findingsRef at fire time (always latest).
  const scheduleSave = useCallback((id: string) => {
    const existing = timers.current.get(id)
    if (existing) clearTimeout(existing)

    const timer = setTimeout(() => {
      timers.current.delete(id)
      const latest = findingsRef.current.find((f) => f.id === id)
      if (latest && isFindingValid(latest) && latest.saveStatus === "draft") {
        persistFindingRef.current?.(latest)
      }
    }, DEBOUNCE_MS)

    timers.current.set(id, timer)
  }, [])

  // Persist one finding: POST for temp ids, PUT for real ids.
  // After success, checks whether the finding was edited during the save
  // (saveStatus would have flipped back to "draft"); if so, re-schedules.
  const persistFinding = useCallback(
    async (finding: Finding) => {
      const isTemp = isTempId(finding.id)
      const idKey = finding.id

      const savedBody = isTemp ? buildCreateBody(finding) : buildUpdateBody(finding)

      setFindings((prev) =>
        prev.map((f) => (f.id === idKey ? { ...f, saveStatus: "saving" as SaveStatus } : f)),
      )

      try {
        let realId = idKey

        if (isTemp) {
          const res = await fetch(`/api/inspections/${inspection.id}/findings`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(savedBody),
          })
          if (res.status === 401) {
            router.push("/login")
            return
          }
          if (!res.ok) {
            setFindings((prev) =>
              prev.map((f) => (f.id === idKey ? { ...f, saveStatus: "error" as SaveStatus } : f)),
            )
            return
          }
          const created = (await res.json()) as { id: string }
          realId = created.id
        } else {
          const res = await fetch(
            `/api/inspections/${inspection.id}/findings/${idKey}`,
            {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(savedBody),
            },
          )
          if (res.status === 401) {
            router.push("/login")
            return
          }
          if (!res.ok) {
            setFindings((prev) =>
              prev.map((f) => (f.id === idKey ? { ...f, saveStatus: "error" as SaveStatus } : f)),
            )
            return
          }
        }

        // Compare current state vs what we sent. If the finding was edited
        // while the request was in flight, saveStatus will be "draft" and we
        // keep it that way so a follow-up save fires.
        setHasSavedOnce(true)
        setFindings((prev) =>
          prev.map((f) => {
            if (f.id !== idKey) return f
            const isDirty = f.saveStatus === "draft"
            return {
              ...f,
              id: realId,
              saveStatus: isDirty ? ("draft" as SaveStatus) : ("saved" as SaveStatus),
            }
          }),
        )

        const current = findingsRef.current.find((f) => f.id === realId)
        if (current?.saveStatus === "draft") {
          scheduleSave(realId)
        }
      } catch {
        setFindings((prev) =>
          prev.map((f) => (f.id === idKey ? { ...f, saveStatus: "error" as SaveStatus } : f)),
        )
      }
    },
    [inspection.id, router, scheduleSave, setFindings],
  )

  // Keep the ref pointing at the latest closure
  persistFindingRef.current = persistFinding

  // -------------------------------------------------------
  // Public API
  // -------------------------------------------------------

  const addFinding = useCallback(
    (section: Section) => {
      setFindings((prev) => [...prev, newFinding(section)])
    },
    [setFindings],
  )

  const updateFinding = useCallback(
    (id: string, patch: Omit<Partial<Finding>, "saveStatus" | "id">) => {
      setFindings((prev) =>
        prev.map((f) => {
          if (f.id !== id) return f
          // If currently saving, revert to draft so persistFinding can detect
          // the edit after its request completes and re-save.
          return { ...f, ...patch, saveStatus: "draft" as SaveStatus }
        }),
      )
      // scheduleSave reads findingsRef at fire time — always latest
      scheduleSave(id)
    },
    [setFindings, scheduleSave],
  )

  const updateFindingLocalOnly = useCallback(
    (id: string, patch: Omit<Partial<Finding>, "saveStatus" | "id">) => {
      setFindings((prev) =>
        prev.map((f) => (f.id !== id ? f : { ...f, ...patch })),
      )
    },
    [setFindings],
  )

  const removeFinding = useCallback(
    async (id: string) => {
      const timer = timers.current.get(id)
      if (timer) {
        clearTimeout(timer)
        timers.current.delete(id)
      }

      // Optimistic removal regardless of temp vs real
      setFindings((prev) => prev.filter((f) => f.id !== id))

      if (!isTempId(id)) {
        try {
          const res = await fetch(`/api/inspections/${inspection.id}/findings/${id}`, {
            method: "DELETE",
          })
          if (res.status === 401) router.push("/login")
        } catch {
          // row is already gone from UI; swallow error
        }
      }
    },
    [inspection.id, router, setFindings],
  )

  const retryFinding = useCallback(
    (id: string) => {
      const finding = findingsRef.current.find((f) => f.id === id)
      if (finding && isFindingValid(finding)) {
        setFindings((prev) =>
          prev.map((f) => (f.id === id ? { ...f, saveStatus: "draft" as SaveStatus } : f)),
        )
        persistFinding(finding)
      }
    },
    [persistFinding, setFindings],
  )

  // Flush all valid pending/errored rows immediately (skips debounce)
  const flushAll = useCallback(() => {
    timers.current.forEach((t) => clearTimeout(t))
    timers.current.clear()

    for (const f of findingsRef.current) {
      if ((f.saveStatus === "draft" || f.saveStatus === "error") && isFindingValid(f)) {
        persistFinding(f)
      }
    }
  }, [persistFinding])

  // -------------------------------------------------------
  // Derived state
  // -------------------------------------------------------

  const findingsBySection = useMemo(() => {
    const map = {} as Record<Section, Finding[]>
    for (const f of findings) {
      ;(map[f.section] ??= []).push(f)
    }
    return map
  }, [findings])

  const counts = useMemo(() => {
    const map = {} as Record<Section, number>
    for (const f of findings) {
      map[f.section] = (map[f.section] ?? 0) + 1
    }
    return map
  }, [findings])

  const sectionsWithErrors = useMemo(() => {
    const set = new Set<Section>()
    for (const f of findings) {
      if (!isFindingValid(f)) set.add(f.section)
    }
    return set
  }, [findings])

  const globalSaveStatus = useMemo((): GlobalSaveStatus => {
    if (findings.some((f) => f.saveStatus === "saving")) return "saving"
    if (findings.some((f) => f.saveStatus === "error")) return "error"
    if (findings.some((f) => f.saveStatus === "draft" && isFindingValid(f))) return "pending"
    if (!hasSavedOnce) return "idle"
    return "all-saved"
  }, [findings, hasSavedOnce])

  // Reset "All changes saved" to idle after 2.5 s — same UX as inspection-detail.
  useEffect(() => {
    if (globalSaveStatus !== "all-saved") return
    const timer = setTimeout(() => setHasSavedOnce(false), 2500)
    return () => clearTimeout(timer)
  }, [globalSaveStatus])

  return {
    inspection,
    findings,
    findingsBySection,
    counts,
    sectionsWithErrors,
    globalSaveStatus,
    addFinding,
    updateFinding,
    updateFindingLocalOnly,
    removeFinding,
    retryFinding,
    flushAll,
    getFindingErrors,
  }
}
