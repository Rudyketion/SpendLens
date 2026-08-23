"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { CategoryBreakdown } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export function CategoryPie({ data }: { data: CategoryBreakdown[] }) {
  const slices = data.map((d) => ({
    name: d.category,
    value: Number(d.total),
    color: d.color,
  }));

  if (slices.length === 0) {
    return (
      <div className="h-64 grid place-items-center text-sm text-muted-foreground">
        No spending data yet. Upload a statement to see the breakdown.
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={slices}
            dataKey="value"
            nameKey="name"
            innerRadius={50}
            outerRadius={90}
            paddingAngle={2}
            strokeWidth={0}
          >
            {slices.map((s, i) => (
              <Cell key={i} fill={s.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "rgb(var(--card))",
              border: "1px solid rgb(var(--border))",
              borderRadius: 10,
              fontSize: 12,
            }}
            formatter={(value: number, name: string) => [formatCurrency(value), name]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
