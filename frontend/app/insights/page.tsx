"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";

import { CategoryPie } from "@/components/category-pie";
import { PageHeader } from "@/components/page-header";
import { SpendingChart } from "@/components/spending-chart";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  CategoryBreakdown,
  Insight,
  TimeseriesPoint,
  api,
} from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [breakdown, setBreakdown] = useState<CategoryBreakdown[]>([]);
  const [series, setSeries] = useState<TimeseriesPoint[]>([]);

  useEffect(() => {
    api.insights().then(setInsights);
    api.categoryBreakdown().then(setBreakdown);
    api.timeseries({ bucket: "month" }).then(setSeries);
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Insights"
        description="The story your money tells, beyond a transaction list."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {insights.map((ins) => (
          <Card key={ins.kind}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" /> {ins.title}
                </span>
                {ins.value ? <Badge>{ins.value}</Badge> : null}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div
                className="text-sm text-muted-foreground"
                dangerouslySetInnerHTML={{
                  __html: ins.body.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
                }}
              />
            </CardContent>
          </Card>
        ))}
        {insights.length === 0 ? (
          <Card>
            <CardContent className="py-6 text-sm text-muted-foreground">
              Upload a statement to start generating insights.
            </CardContent>
          </Card>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Monthly cash flow</CardTitle>
          <CardDescription>How each month has shaped up.</CardDescription>
        </CardHeader>
        <CardContent>
          <SpendingChart data={series} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top categories all-time</CardTitle>
        </CardHeader>
        <CardContent>
          <CategoryPie data={breakdown} />
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
            {breakdown.map((c) => (
              <div
                key={c.category}
                className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className="h-2.5 w-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: c.color }}
                  />
                  <span className="truncate">{c.category}</span>
                </div>
                <div className="flex items-center gap-3 tabular-nums">
                  <span className="text-muted-foreground">{(c.share * 100).toFixed(0)}%</span>
                  <span className="font-medium">{formatCurrency(Number(c.total))}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
