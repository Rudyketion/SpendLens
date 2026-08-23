"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { TimeseriesPoint } from "@/lib/api";
import { formatCurrency, formatShortNumber, shortDate } from "@/lib/utils";

export function SpendingChart({ data }: { data: TimeseriesPoint[] }) {
  const chart = data.map((d) => ({
    bucket: d.bucket,
    income: Number(d.income),
    expense: Number(d.expense),
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <AreaChart data={chart} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="incomeFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="expenseFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgb(var(--border))" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="bucket"
            tickFormatter={shortDate}
            stroke="rgb(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tickFormatter={(v) => `$${formatShortNumber(v)}`}
            stroke="rgb(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            width={50}
          />
          <Tooltip
            contentStyle={{
              background: "rgb(var(--card))",
              border: "1px solid rgb(var(--border))",
              borderRadius: 10,
              fontSize: 12,
            }}
            labelFormatter={(v) => shortDate(String(v))}
            formatter={(value: number, key: string) => [formatCurrency(value), key === "income" ? "Income" : "Expense"]}
          />
          <Area
            type="monotone"
            dataKey="income"
            stroke="#10b981"
            fill="url(#incomeFill)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="expense"
            stroke="#f43f5e"
            fill="url(#expenseFill)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
