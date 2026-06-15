// apps/web/app/page.tsx
import HealthStatus from '@/components/HealthStatus'
import InspectionList from '@/components/InspectionList'
import PropertyCount from '@/components/PropertyCount'

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">MCAG Technologies</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Florida Home Inspector Reports
          </p>
        </div>
        <HealthStatus />
      </div>

      <div className="mb-8">
        <PropertyCount />
      </div>

      <section>
        <h2 className="mb-4 text-lg font-semibold">Recent Inspections</h2>
        <InspectionList />
      </section>
    </main>
  )
}
