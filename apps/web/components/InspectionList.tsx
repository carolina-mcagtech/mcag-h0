// apps/web/components/InspectionList.tsx
'use client'

import { useEffect, useState } from 'react'

type InspectionStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
type InspectionType =
  | 'FULL_INSPECTION'
  | 'WIND_MITIGATION'
  | 'FOUR_POINT'
  | 'MOLD_INSPECTION'
  | 'TERMITES'
  | 'ROOF_CERTIFICATION'
  | 'OPENING_PROTECTION'
  | 'SEWER_INSPECTION'

interface Inspection {
  id: string
  property_id: string
  status: InspectionStatus
  scheduled_date: string
  inspection_types: InspectionType[]
  total_fee: string
}

interface Property {
  id: string
  street: string
  city: string
  state: string
  zip_code: string
}

const STATUS_LABELS: Record<InspectionStatus, string> = {
  SCHEDULED: 'Scheduled',
  IN_PROGRESS: 'In Progress',
  COMPLETED: 'Completed',
  CANCELLED: 'Cancelled',
}

const STATUS_COLORS: Record<InspectionStatus, string> = {
  SCHEDULED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  COMPLETED: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  CANCELLED: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

const TYPE_LABELS: Record<InspectionType, string> = {
  FULL_INSPECTION: 'Full',
  WIND_MITIGATION: 'Wind Mit',
  FOUR_POINT: '4-Point',
  MOLD_INSPECTION: 'Mold',
  TERMITES: 'Termites',
  ROOF_CERTIFICATION: 'Roof Cert',
  OPENING_PROTECTION: 'Opening Prot',
  SEWER_INSPECTION: 'Sewer',
}

function SkeletonRow() {
  return (
    <tr>
      {[80, 160, 120, 90, 60].map((w, i) => (
        <td key={i} className="px-4 py-3">
          <div
            className="h-4 animate-pulse rounded bg-gray-200 dark:bg-gray-700"
            style={{ width: w }}
          />
        </td>
      ))}
    </tr>
  )
}

export default function InspectionList() {
  const [inspections, setInspections] = useState<Inspection[] | null>(null)
  const [propertyMap, setPropertyMap] = useState<Map<string, string>>(new Map())
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([
      fetch('/api/inspections', { cache: 'no-store' }).then((r) => {
        if (!r.ok) throw new Error('inspections failed')
        return r.json() as Promise<Inspection[]>
      }),
      fetch('/api/properties', { cache: 'no-store' }).then((r) => {
        if (!r.ok) throw new Error('properties failed')
        return r.json() as Promise<Property[]>
      }),
    ])
      .then(([insp, props]) => {
        const map = new Map(props.map((p) => [p.id, `${p.street}, ${p.city}`]))
        setPropertyMap(map)
        setInspections(insp)
      })
      .catch(() => setError(true))
  }, [])

  if (error) {
    return (
      <p className="rounded-lg border border-red-200 px-4 py-3 text-sm text-red-600 dark:border-red-900 dark:text-red-400">
        Failed to load inspections.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
      <table className="dashboard-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Property</th>
            <th>Types</th>
            <th>Status</th>
            <th className="text-right">Fee</th>
          </tr>
        </thead>
        <tbody>
          {inspections === null ? (
            <>
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
            </>
          ) : inspections.length === 0 ? (
            <tr>
              <td
                colSpan={5}
                className="px-4 py-10 text-center text-sm text-gray-500 dark:text-gray-400"
              >
                No inspections yet
              </td>
            </tr>
          ) : (
            inspections.slice(0, 10).map((insp) => (
              <tr key={insp.id}>
                <td className="px-4 py-3 text-sm">{insp.scheduled_date}</td>
                <td className="px-4 py-3 text-sm">
                  {propertyMap.get(insp.property_id) ??
                    `${insp.property_id.slice(0, 8)}…`}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {insp.inspection_types.map((t) => (
                      <span
                        key={t}
                        className="rounded bg-gray-100 px-1.5 py-0.5 text-xs dark:bg-gray-800"
                      >
                        {TYPE_LABELS[t]}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[insp.status]}`}
                  >
                    {STATUS_LABELS[insp.status]}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-sm font-medium">
                  ${Number(insp.total_fee).toFixed(2)}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
