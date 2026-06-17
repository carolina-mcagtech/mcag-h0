import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const ROWS = Array.from({ length: 6 })

export function InspectionsSkeleton() {
  return (
    <>
      {/* Desktop skeleton */}
      <div className="hidden overflow-hidden rounded-lg border border-border bg-card md:block">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50 hover:bg-muted/50">
              <TableHead className="pl-6">Property Address</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Scheduled</TableHead>
              <TableHead>Inspection Types</TableHead>
              <TableHead className="pr-6 text-right">Fee</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {ROWS.map((_, i) => (
              <TableRow key={i} className="hover:bg-transparent">
                <TableCell className="pl-6">
                  <Skeleton className="h-4 w-56" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-5 w-20 rounded-full" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-36" />
                </TableCell>
                <TableCell>
                  <div className="flex gap-1.5">
                    <Skeleton className="h-5 w-24 rounded-md" />
                    <Skeleton className="h-5 w-20 rounded-md" />
                  </div>
                </TableCell>
                <TableCell className="pr-6">
                  <div className="flex justify-end">
                    <Skeleton className="h-4 w-16" />
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile skeleton */}
      <div className="flex flex-col gap-3 md:hidden">
        {ROWS.slice(0, 4).map((_, i) => (
          <div
            key={i}
            className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4"
          >
            <Skeleton className="h-4 w-3/4" />
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-20 rounded-full" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-4 w-40" />
            <div className="flex gap-1.5">
              <Skeleton className="h-5 w-24 rounded-md" />
              <Skeleton className="h-5 w-20 rounded-md" />
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
