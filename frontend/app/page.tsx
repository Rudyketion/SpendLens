"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  Banknote,
  PiggyBank,
  Receipt,
  Sparkles,
} from "lucide-react";

import { CategoryPie } from "@/components/category-pie";
import { PageHeader } from "@/components/page-header";
import { SpendingChart } from "@/components/spending-chart";
import { StatCard } from "@/components/stat-card";
import { TransactionsTable } from "@/components/transactions-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  Totals,
  Transaction,
  api,
} from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

type Range = "30d" | "90d" | "ytd" | "all";

function rangeToDates(range: Range): { start?: string; end?: string } {
  const today = new Date();
  const end = today.toISOString().slice(0, 10);
  if (range === "all") return {};
  if (range === "ytd") {
    return { start: `${today.getUTCFullYear()}-01-01`, end };
  }
  const days = range === "30d" ? 30 : 90;
  const start = new Date(today);
  start.setUTCDate(start.getUTCDate() - days);
  return { start: start.toISOString().slice(0, 10), end };
}

export default function DashboardPage() {
  const [range, setRange] = useState<Range>("30d");
  const params = useMemo(() => rangeToDates(range), [range]);

  const [totals, setTotals] = useState<Totals | null>(null);
  const [breakdown, setBreakdown] = useState<CategoryBreakdown[]>([]);
  const [series, setSeries] = useState<TimeseriesPoint[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [recent, setRecent] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [t, b, ts, ins, recent] = await Promise.all([
        api.totals(params),
        api.categoryBreakdown(params),
        api.timeseries({ ...params, bucket: "day" }),
        api.insights(params),
        api.transactions({ ...params, limit: 8 }),
      ]);
      setTotals(t);
      setBreakdown(b);
      setSeries(ts);
      setInsights(ins);
      setRecent(recent);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    load();
  }, [load]);

  const expenseAbs = totals ? Math.abs(Number(totals.expense)) : 0;
  const income = totals ? Number(totals.income) : 0;
  const net = totals ? Number(totals.net) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="A quick read on cash flow, categories, and what stood out this period."
        actions={
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
            {(["30d", "90d", "ytd", "all"] as Range[]).map((r) => (
              <Button
                key={r}
                variant={range === r ? "default" : "ghost"}
                size="sm"
                onClick={() => setRange(r)}
                className="h-7 px-2"
              >
                {r.toUpperCase()}
              </Button>
            ))}
          </div>
        }
      />

      {error ? (
        <Card className="border-rose-200 bg-rose-50 dark:border-rose-900 dark:bg-rose-950/30">
          <CardContent className="text-sm text-rose-700 dark:text-rose-300 py-4">
            Couldn&apos;t load data: {error}. Make sure the backend is running on port 8000.
          </CardContent>
        </Card>
      ) : null}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Income"
          value={formatCurrency(income)}
          icon={<ArrowUpRight className="h-4 w-4" />}
          tone="positive"
          hint={totals ? `${totals.transaction_count} transactions` : "—"}
        />
        <StatCard
          label="Spending"
          value={formatCurrency(expenseAbs)}
          icon={<ArrowDownRight className="h-4 w-4" />}
          tone="negative"
        />
        <StatCard
          label="Net"
          value={formatCurrency(net)}
          icon={<PiggyBank className="h-4 w-4" />}
          tone={net >= 0 ? "positive" : "negative"}
          hint={income > 0 ? `${((net / income) * 100).toFixed(1)}% savings rate` : undefined}
        />
        <StatCard
          label="Top category"
          value={breakdown[0] ? breakdown[0].category : "—"}
          icon={<Receipt className="h-4 w-4" />}
          hint={
            breakdown[0]
              ? `${formatCurrency(Number(breakdown[0].total))} · ${(breakdown[0].share * 100).toFixed(0)}% of spend`
              : undefined
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Cash flow</CardTitle>
            <CardDescription>Daily income vs expense over the selected range.</CardDescription>
          </CardHeader>
          <CardContent>
            <SpendingChart data={series} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Spending by category</CardTitle>
            <CardDescription>Where your outflows actually go.</CardDescription>
          </CardHeader>
          <CardContent>
            <CategoryPie data={breakdown} />
            <div className="mt-4 space-y-2 max-h-44 overflow-y-auto pr-1">
              {breakdown.slice(0, 8).map((c) => (
                <div key={c.category} className="flex items-center justify-between text-sm">
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

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" /> Insights
          </CardTitle>
          <CardDescription>Automatic call-outs from your transactions.</CardDescription>
        </CardHeader>
        <CardContent>
          {insights.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              {loading ? "Crunching numbers…" : "No insights yet — upload a statement to see what stands out."}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {insights.map((ins) => (
                <div
                  key={ins.kind}
                  className="rounded-xl border border-border bg-muted/30 p-4"
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-sm font-semibold">{ins.title}</div>
                    {ins.value ? <Badge>{ins.value}</Badge> : null}
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    dangerouslySetInnerHTML={{
                      __html: ins.body.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
                    }}
                  />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Banknote className="h-4 w-4" /> Recent transactions
          </CardTitle>
          <CardDescription>Latest 8 in this range.</CardDescription>
        </CardHeader>
        <CardContent>
          <TransactionsTable rows={recent} onChange={load} />
        </CardContent>
      </Card>
    </div>
  );
}
