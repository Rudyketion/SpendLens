"use client";

import { useState } from "react";
import { Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Transaction, api } from "@/lib/api";
import { cn, formatCurrency, formatDate } from "@/lib/utils";

export function TransactionsTable({
  rows,
  onChange,
}: {
  rows: Transaction[];
  onChange?: () => void;
}) {
  const [busyId, setBusyId] = useState<number | null>(null);

  async function remove(id: number) {
    setBusyId(id);
    try {
      await api.deleteTransaction(id);
      onChange?.();
    } finally {
      setBusyId(null);
    }
  }

  if (rows.length === 0) {
    return (
      <div className="text-center text-sm text-muted-foreground py-12">
        No transactions match the current filters.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-muted-foreground">
          <tr className="text-left">
            <th className="px-4 py-2.5 font-medium">Date</th>
            <th className="px-4 py-2.5 font-medium">Description</th>
            <th className="px-4 py-2.5 font-medium">Category</th>
            <th className="px-4 py-2.5 font-medium text-right">Amount</th>
            <th className="w-10" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((tx) => {
            const amount = Number(tx.amount);
            return (
              <tr key={tx.id} className="hover:bg-accent/40 transition-colors">
                <td className="px-4 py-2.5 whitespace-nowrap text-muted-foreground tabular-nums">
                  {formatDate(tx.occurred_on)}
                </td>
                <td className="px-4 py-2.5">
                  <div className="font-medium leading-tight">{tx.description}</div>
                  {tx.merchant && tx.merchant !== tx.description ? (
                    <div className="text-xs text-muted-foreground">{tx.merchant}</div>
                  ) : null}
                </td>
                <td className="px-4 py-2.5">
                  {tx.category ? (
                    <Badge color={tx.category.color}>{tx.category.name}</Badge>
                  ) : (
                    <Badge>Uncategorized</Badge>
                  )}
                </td>
                <td
                  className={cn(
                    "px-4 py-2.5 text-right tabular-nums font-medium",
                    amount > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-foreground",
                  )}
                >
                  {amount > 0 ? "+" : ""}
                  {formatCurrency(amount, tx.currency)}
                </td>
                <td className="px-2 py-2.5 text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(tx.id)}
                    disabled={busyId === tx.id}
                    aria-label="Delete transaction"
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
