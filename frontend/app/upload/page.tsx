"use client";

import { useCallback, useEffect, useState } from "react";
import { FileText, Trash2 } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { UploadZone } from "@/components/upload-zone";
import { Statement, api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function UploadPage() {
  const [statements, setStatements] = useState<Statement[]>([]);

  const load = useCallback(async () => {
    try {
      setStatements(await api.statements());
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function remove(id: number) {
    await api.deleteStatement(id);
    load();
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload statement"
        description="Drop a CSV or PDF from your bank. SpendLens parses, categorizes, and stores every row."
      />

      <Card>
        <CardContent className="pt-5">
          <UploadZone onUploaded={() => load()} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Uploaded statements</CardTitle>
          <CardDescription>Remove a file to delete all its transactions.</CardDescription>
        </CardHeader>
        <CardContent>
          {statements.length === 0 ? (
            <div className="text-sm text-muted-foreground py-6 text-center">
              No statements uploaded yet.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {statements.map((s) => (
                <li key={s.id} className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-muted text-muted-foreground">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-medium truncate">{s.filename}</div>
                      <div className="text-xs text-muted-foreground">
                        {s.file_type.toUpperCase()} · {s.row_count} rows · uploaded{" "}
                        {formatDate(s.uploaded_at)}
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => remove(s.id)} aria-label="Delete">
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Supported formats</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            <strong className="text-foreground">CSV / TSV:</strong> any export with columns for date,
            description, and either a single amount column or separate debit/credit columns. Common
            bank exports work out of the box.
          </p>
          <p>
            <strong className="text-foreground">PDF:</strong> table-based statements are extracted via
            pdfplumber; line-based statements fall back to regex parsing.
          </p>
          <p>
            Once parsed, every row is sent in a single batch to Claude for category prediction. If no
            API key is set, the deterministic keyword classifier kicks in so the app keeps working.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
