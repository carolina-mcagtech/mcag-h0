import { ClipboardListIcon } from "lucide-react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import {
  formatSectionName,
  type FindingsSummary as FindingsSummaryData,
} from "@/lib/inspection-detail"

export function FindingsSummary({ data }: { data: FindingsSummaryData }) {
  const sections = Object.entries(data)
  const total = sections.reduce((acc, [, v]) => acc + v.total, 0)
  const defective = sections.reduce((acc, [, v]) => acc + v.defective, 0)
  const isEmpty = sections.length === 0 || total === 0

  return (
    <Card className="border-primary/20 bg-card">
      <CardHeader>
        <div className="flex items-center gap-2.5">
          <span className="flex size-8 items-center justify-center rounded-md bg-primary/10 text-primary">
            <ClipboardListIcon className="size-4" />
          </span>
          <CardTitle className="text-base">Findings Summary</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <p className="text-sm text-muted-foreground">
            No findings recorded yet
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            <p className="text-2xl font-semibold tracking-tight text-foreground">
              {total} findings
              <span className="px-2 text-muted-foreground">·</span>
              <span
                className={cn(
                  defective > 0 ? "text-destructive" : "text-muted-foreground",
                )}
              >
                {defective} defective
              </span>
            </p>
            <Separator />
            <ul className="flex flex-col gap-2.5">
              {sections.map(([name, counts]) => (
                <li
                  key={name}
                  className="flex items-center justify-between gap-4 text-sm"
                >
                  <span className="font-medium text-foreground">
                    {formatSectionName(name)}
                  </span>
                  <span className="flex items-center gap-3 tabular-nums">
                    <span className="text-muted-foreground">
                      {counts.total} total
                    </span>
                    <span
                      className={cn(
                        "min-w-[5rem] text-right",
                        counts.defective > 0
                          ? "font-medium text-destructive"
                          : "text-muted-foreground",
                      )}
                    >
                      {counts.defective} defective
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
