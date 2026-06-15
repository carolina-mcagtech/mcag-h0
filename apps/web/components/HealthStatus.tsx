// apps/web/components/HealthStatus.tsx
'use client'

import { useEffect, useState } from 'react'

type Status = 'loading' | 'connected' | 'error'

export default function HealthStatus() {
  const [status, setStatus] = useState<Status>('loading')

  useEffect(() => {
    fetch('/api/health', { cache: 'no-store' })
      .then((res) => {
        setStatus(res.ok ? 'connected' : 'error')
      })
      .catch(() => setStatus('error'))
  }, [])

  const label: Record<Status, string> = {
    loading: 'API: checking…',
    connected: 'API: connected',
    error: 'API: error',
  }

  const dot: Record<Status, string> = {
    loading: 'bg-gray-400 animate-pulse',
    connected: 'bg-green-500',
    error: 'bg-red-500',
  }

  const text: Record<Status, string> = {
    loading: 'text-gray-500',
    connected: 'text-green-600 dark:text-green-400',
    error: 'text-red-600 dark:text-red-400',
  }

  return (
    <div className="flex items-center gap-2 rounded-lg border border-gray-200 px-4 py-3 dark:border-gray-800">
      <span className={`h-2 w-2 rounded-full ${dot[status]}`} />
      <span className={`text-sm font-medium ${text[status]}`}>
        {label[status]}
      </span>
    </div>
  )
}
