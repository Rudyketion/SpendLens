"use client";

import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { TransactionsTable } from "@/components/transactions-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Category, Transaction, api } from "@/lib/api";

export default function TransactionsPage() {
  const [rows, setRows] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [q, setQ] = useState("");
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await api.transactions({ q, category_id: categoryId, limit: 500 });
      setRows(rows);
    } finally {
      setLoading(false);
    }
  }, [q, categoryId]);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transactions"
        description="Search, filter, and clean up imported transactions."
      />

      <Card>
        <CardContent className="pt-5">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search description or merchant…"
                className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant={categoryId === undefined ? "default" : "outline"}
                size="sm"
                onClick={() => setCategoryId(undefined)}
              >
                All
              </Button>
              {categories.map((c) => (
                <Button
                  key={c.id}
                  variant={categoryId === c.id ? "default" : "outline"}
                  size="sm"
                  onClick={() => setCategoryId(c.id)}
                  style={
                    categoryId === c.id
                      ? { backgroundColor: c.color, borderColor: c.color }
                      : undefined
                  }
                >
                  {c.name}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5">
          {loading ? (
            <div className="text-sm text-muted-foreground py-6 text-center">Loading…</div>
          ) : (
            <TransactionsTable rows={rows} onChange={load} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
