/**
 * Document Viewer with approval flow — plan IDE Frontend Phase 1.3
 * Renders markdown content, supports approve / request-changes flow.
 */
import React, { useMemo, useState } from "react";
import type { DocumentResponse } from "@/lib/society-api";
import { approveDocument, documentFeedback } from "@/lib/society-api";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface DocumentViewerProps {
  document: DocumentResponse;
  onApprove?: () => void;
  onReject?: (feedback: string) => void;
}

// ── Lightweight markdown → HTML renderer (no external deps needed) ─────────
function renderMarkdown(md: string): string {
  return (
    md
      // Headings
      .replace(/^#### (.+)$/gm, "<h4>$1</h4>")
      .replace(/^### (.+)$/gm, "<h3>$1</h3>")
      .replace(/^## (.+)$/gm, "<h2>$1</h2>")
      .replace(/^# (.+)$/gm, "<h1>$1</h1>")
      // Bold / italic
      .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      // Inline code
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      // Code blocks (``` ... ```)
      .replace(/```[\w]*\n?([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
      // Horizontal rule
      .replace(/^---$/gm, "<hr />")
      // Unordered list items
      .replace(/^\s*[-*] (.+)$/gm, "<li>$1</li>")
      // Ordered list items
      .replace(/^\s*\d+\. (.+)$/gm, "<li>$1</li>")
      // Paragraphs (blank-line separated, not inside block elements)
      .replace(/\n{2,}/g, "\n</p><p>\n")
      .replace(/^(?!<[hHplLcCpP])(.+)$/gm, (line) =>
        line.startsWith("<") ? line : `<p>${line}</p>`,
      )
  );
}

const DOC_TYPE_LABELS: Record<string, string> = {
  prd: "Product Requirements",
  system_design: "System Design",
  api_spec: "API Specification",
  task_breakdown: "Task Breakdown",
  code_implementation: "Code Implementation",
  test_plan: "Test Plan",
  deployment: "Deployment Guide",
  user_docs: "User Documentation",
};

export function DocumentViewer({ document, onApprove, onReject }: DocumentViewerProps) {
  const [feedback, setFeedback] = useState("");
  const [showFeedback, setShowFeedback] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    setLoading(true);
    try {
      await approveDocument(document.doc_id);
      onApprove?.();
    } finally {
      setLoading(false);
    }
  };

  const handleSendFeedback = async () => {
    if (!feedback.trim()) return;
    setLoading(true);
    try {
      await documentFeedback(document.doc_id, feedback);
      setShowFeedback(false);
      setFeedback("");
      onReject?.(feedback);
    } finally {
      setLoading(false);
    }
  };

  const statusClass =
    document.status === "approved"
      ? "bg-green-500/20 text-green-400 border-green-500/30"
      : document.status === "rejected"
        ? "bg-red-500/20 text-red-400 border-red-500/30"
        : "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";

  const docTypeLabel = DOC_TYPE_LABELS[document.doc_type] ?? document.doc_type;

  // Convert markdown to HTML for rendering
  const htmlContent = useMemo(
    () => renderMarkdown(document.content_markdown),
    [document.content_markdown],
  );

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="p-4 bg-gray-800 border-b border-gray-700">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-white">{document.title}</h2>
            <div className="flex flex-wrap gap-3 mt-1 text-xs text-gray-400">
              <span className="bg-gray-700 px-2 py-0.5 rounded">{docTypeLabel}</span>
              <span>by {document.created_by}</span>
              <span>v{document.version}</span>
              <span className={`px-2 py-0.5 rounded border ${statusClass}`}>
                {document.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-6">
        <div
          className="max-w-4xl prose-doc"
          /* eslint-disable-next-line react/no-danger -- sanitised by our own renderer */
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      </ScrollArea>

      {/* Approval controls (only shown for draft docs) */}
      {document.status === "draft" && (onApprove || onReject) && (
        <div className="p-4 bg-gray-800 border-t border-gray-700">
          {!showFeedback ? (
            <div className="flex gap-3">
              <Button
                onClick={handleApprove}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                {loading ? "Approving…" : "Approve"}
              </Button>
              <Button
                onClick={() => setShowFeedback(true)}
                variant="outline"
                className="border-yellow-600 text-yellow-400 hover:bg-yellow-600/10"
              >
                Request changes
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              <textarea
                rows={3}
                placeholder="What needs to change?"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder:text-gray-500 resize-none focus:outline-none focus:border-blue-500"
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleSendFeedback}
                  disabled={loading || !feedback.trim()}
                >
                  {loading ? "Sending…" : "Send feedback"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowFeedback(false);
                    setFeedback("");
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
