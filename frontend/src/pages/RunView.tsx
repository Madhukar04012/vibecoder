/**
 * Run view: live agent activity + live document typing + document viewer
 */
import React, { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { AgentDashboard } from "@/components/society/AgentDashboard";
import { DocumentViewer } from "@/components/society/DocumentViewer";
import { LiveDocPanel } from "@/components/society/LiveDocPanel";
import { getDocument, type DocumentResponse } from "@/lib/society-api";

export default function RunView() {
  const [searchParams] = useSearchParams();
  const runId = searchParams.get("run_id") ?? "";

  const [selectedDoc, setSelectedDoc] = useState<DocumentResponse | null>(null);
  const [loadingDoc, setLoadingDoc] = useState(false);

  if (!runId) {
    return <div className="p-8 text-gray-400">No run_id in URL.</div>;
  }

  const openDoc = (docId: string) => {
    setLoadingDoc(true);
    getDocument(docId)
      .then(setSelectedDoc)
      .catch(() => {/* document may not be persisted yet, ignore */})
      .finally(() => setLoadingDoc(false));
  };

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">

      {/* ── Left sidebar: agent status ────────────────────────────── */}
      <aside className="w-72 flex-shrink-0 border-r border-gray-800 flex flex-col overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/60 flex-shrink-0">
          <h1 className="text-sm font-semibold text-gray-200">
            Run:{" "}
            <span className="font-mono text-blue-400">{runId.slice(0, 14)}…</span>
          </h1>
        </div>
        <div className="flex-1 overflow-auto">
          <AgentDashboard runId={runId} onDocumentClick={openDoc} />
        </div>
      </aside>

      {/* ── Main area: live typing OR document viewer ─────────────── */}
      <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {selectedDoc ? (
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* header with back button */}
            <div className="flex items-center gap-3 px-5 py-3 border-b border-gray-800 bg-gray-900/60 flex-shrink-0">
              <button
                type="button"
                onClick={() => setSelectedDoc(null)}
                className="text-xs text-gray-400 hover:text-white flex items-center gap-1 transition-colors"
              >
                ← Live view
              </button>
              <span className="text-gray-600 text-xs">|</span>
              <span className="text-sm font-medium text-gray-200">{selectedDoc.title}</span>
            </div>
            <div className="flex-1 overflow-auto">
              <DocumentViewer
                document={selectedDoc}
                onApprove={() =>
                  setSelectedDoc((prev) => (prev ? { ...prev, status: "approved" } : null))
                }
              />
            </div>
          </div>
        ) : (
          <LiveDocPanel
            runId={runId}
            onDocumentReady={openDoc}
          />
        )}
        {loadingDoc && (
          <div className="absolute inset-0 bg-gray-950/70 flex items-center justify-center pointer-events-none">
            <span className="text-gray-400 text-sm animate-pulse">Loading document…</span>
          </div>
        )}
      </main>
    </div>
  );
}
