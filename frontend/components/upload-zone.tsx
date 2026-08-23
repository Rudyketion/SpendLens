"use client";

import { ChangeEvent, DragEvent, useState } from "react";
import { CheckCircle2, FileUp, Loader2, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { UploadResult, api } from "@/lib/api";
import { cn } from "@/lib/utils";

export function UploadZone({ onUploaded }: { onUploaded?: (r: UploadResult) => void }) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const file = files[0];
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.uploadStatement(file);
      setResult(res);
      onUploaded?.(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  function onDrop(e: DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  function onChange(e: ChangeEvent<HTMLInputElement>) {
    handleFiles(e.target.files);
    e.target.value = "";
  }

  return (
    <div className="space-y-4">
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed cursor-pointer",
          "transition-colors px-6 py-12 text-center",
          dragging
            ? "border-primary bg-primary/5"
            : "border-border bg-card hover:bg-accent/40",
        )}
      >
        <div className="grid h-12 w-12 place-items-center rounded-full bg-primary/10 text-primary">
          {busy ? <Loader2 className="h-6 w-6 animate-spin" /> : <FileUp className="h-6 w-6" />}
        </div>
        <div>
          <div className="font-medium">
            {busy ? "Parsing your statement…" : "Drop a CSV or PDF statement"}
          </div>
          <div className="text-sm text-muted-foreground">
            We&apos;ll parse it, categorize every line, and add it to your dashboard.
          </div>
        </div>
        <Button type="button" variant="outline" size="sm" disabled={busy}>
          {busy ? "Working…" : "Choose file"}
        </Button>
        <input
          type="file"
          accept=".csv,.tsv,.pdf"
          className="hidden"
          onChange={onChange}
          disabled={busy}
        />
      </label>

      {result ? (
        <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm dark:border-emerald-900 dark:bg-emerald-950/30">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 mt-0.5" />
          <div>
            <div className="font-medium text-emerald-700 dark:text-emerald-300">
              Imported {result.imported} transactions from {result.statement.filename}
            </div>
            <div className="text-emerald-700/80 dark:text-emerald-400/80">
              {result.categorized} auto-categorized · {result.imported - result.categorized} marked &ldquo;Other&rdquo;
            </div>
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm dark:border-rose-900 dark:bg-rose-950/30">
          <XCircle className="h-5 w-5 text-rose-600 mt-0.5" />
          <div className="text-rose-700 dark:text-rose-300">{error}</div>
        </div>
      ) : null}
    </div>
  );
}
