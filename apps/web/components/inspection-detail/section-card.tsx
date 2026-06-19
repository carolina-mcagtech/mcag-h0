import type { LucideIcon } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

export function SectionCard({
  icon: Icon,
  title,
  description,
  children,
  columns = 2,
}: {
  icon: LucideIcon
  title: string
  description?: string
  children: React.ReactNode
  columns?: 1 | 2 | 3
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2.5">
          <span className="flex size-8 items-center justify-center rounded-md bg-accent text-accent-foreground">
            <Icon className="size-4" />
          </span>
          <div className="flex flex-col gap-0.5">
            <CardTitle className="text-base">{title}</CardTitle>
            {description ? (
              <CardDescription>{description}</CardDescription>
            ) : null}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            "grid grid-cols-1 gap-4 [&>*]:min-w-0",
            columns === 2 && "sm:grid-cols-2",
            columns === 3 && "sm:grid-cols-2 lg:grid-cols-3",
          )}
        >
          {children}
        </div>
      </CardContent>
    </Card>
  )
}
