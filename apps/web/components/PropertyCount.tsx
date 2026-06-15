// apps/web/components/PropertyCount.tsx
'use client'

import { useEffect, useState } from 'react'
import { tenantHeaders } from '@/lib/api'

type Property = { id: string }

export default function PropertyCount() {
  const [count, setCount] = useState<number | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/properties', { cache: 'no-store', headers: tenantHeaders })
      .then((res) => {
        if (!res.ok) throw new Error('failed')
        return res.json() as Promise<Property[]>
      })
      .then((data) => setCount(data.length))
      .catch(() => setError(true))
  }, [])

  if (error) {
    return (
      <p className="text-sm text-red-600 dark:text-red-400">
        Failed to load property count.
      </p>
    )
  }

  if (count === null) {
    return <div className="h-8 w-44 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
  }

  return (
    <p className="text-sm text-gray-600 dark:text-gray-400">
      <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {count}
      </span>{' '}
      {count === 1 ? 'property' : 'properties'} on file
    </p>
  )
}
