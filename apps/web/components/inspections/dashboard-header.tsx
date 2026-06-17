import { ShieldCheck, ChevronDown, User, Settings, LogOut } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function DashboardHeader() {
  const inspectorName = "Marcus Reyes"

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-card/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheck className="size-5" aria-hidden="true" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-foreground">
            Inspect<span className="text-primary">IQ</span>
          </span>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Avatar className="size-8">
              <AvatarFallback className="bg-secondary text-xs font-medium text-secondary-foreground">
                MR
              </AvatarFallback>
            </Avatar>
            <span className="hidden font-medium text-foreground sm:inline">
              {inspectorName}
            </span>
            <ChevronDown
              className="size-4 text-muted-foreground"
              aria-hidden="true"
            />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel className="flex flex-col gap-0.5">
              <span>{inspectorName}</span>
              <span className="text-xs font-normal text-muted-foreground">
                FL License #HI-7421
              </span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="size-4" aria-hidden="true" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="size-4" aria-hidden="true" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <LogOut className="size-4" aria-hidden="true" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
