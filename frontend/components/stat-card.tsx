import { ReactNode } from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  hint,
  icon,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: ReactNode;
  tone?: "default" | "positive" | "negative";
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div className="text-sm font-medium text-muted-foreground">{label}</div>
        {icon ? (
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-muted text-muted-foreground">
            {icon}
          </div>
        ) : null}
      </div>
      <div
        className={cn(
          "mt-2 text-2xl font-semibold tracking-tight tabular-nums",
          tone === "positive" && "text-emerald-600 dark:text-emerald-400",
          tone === "negative" && "text-rose-600 dark:text-rose-400",
        )}
      >
        {value}
      </div>
      {hint ? <div className="mt-1 text-xs text-muted-foreground">{hint}</div> : null}
    </Card>
  );
}
