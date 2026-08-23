"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ListChecks, Sparkles, Upload, Wallet } from "lucide-react";

import { cn } from "@/lib/utils";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions", icon: ListChecks },
  { href: "/insights", label: "Insights", icon: Sparkles },
  { href: "/upload", label: "Upload", icon: Upload },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-border bg-card/60 backdrop-blur">
      <div className="px-6 py-6 flex items-center gap-2">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary text-primary-foreground">
          <Wallet className="h-5 w-5" />
        </div>
        <div>
          <div className="text-base font-semibold tracking-tight">SpendLens</div>
          <div className="text-xs text-muted-foreground">Personal finance, clarified</div>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-5 py-5 text-xs text-muted-foreground border-t border-border">
        <div className="font-medium text-foreground mb-1">AI categorization</div>
        Drops a CSV/PDF here, Claude tags every transaction in seconds.
      </div>
    </aside>
  );
}

export function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="lg:hidden sticky top-0 z-30 flex items-center gap-1 overflow-x-auto border-b border-border bg-card/80 backdrop-blur px-3 py-2">
      {items.map((item) => {
        const Icon = item.icon;
        const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm",
              active ? "bg-primary text-primary-foreground" : "text-muted-foreground",
            )}
          >
            <Icon className="h-4 w-4" /> {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
