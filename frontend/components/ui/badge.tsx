import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

export function Badge({
  className,
  color,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { color?: string }) {
  const style = color
    ? { backgroundColor: `${color}1a`, color, borderColor: `${color}40` }
    : undefined;
  return (
    <span
      style={style}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        !color && "border-border bg-muted text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}
