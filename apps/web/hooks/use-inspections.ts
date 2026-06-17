// apps/web/hooks/use-inspections.ts
"use client"

import { useEffect, useState } from "react"
import { MOCK_INSPECTIONS, type Inspection } from "@/lib/inspections"

interface UseInspectionsResult {
  inspections: Inspection[]
  isLoading: boolean
}

// Swap the mock body for a real fetch / SWR call later without touching the UI.
export function useInspections(): UseInspectionsResult {
  const [inspections, setInspections] = useState<Inspection[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setInspections(MOCK_INSPECTIONS)
      setIsLoading(false)
    }, 900)
    return () => clearTimeout(timer)
  }, [])

  return { inspections, isLoading }
}
