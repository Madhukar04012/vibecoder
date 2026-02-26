/**
 * Chat attachment types, constants, and validation helpers.
 * Extracted from AtomsChatPanel so InputArea and any future components can
 * share them without circular dependencies.
 */

export interface ChatAttachment {
  id: string;
  name: string;
  type: 'file' | 'image' | 'code' | 'text';
  content: string;
  size: number;
  preview?: string;
  mimeType?: string;
}

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB per file
export const MAX_TOTAL_SIZE = 25 * 1024 * 1024; // 25MB total

export const ALLOWED_MIME_TYPES = new Set([
  'text/plain', 'text/markdown', 'text/html', 'text/css', 'text/javascript',
  'application/json', 'application/yaml', 'application/xml',
  'image/png', 'image/jpeg', 'image/gif', 'image/svg+xml', 'image/webp',
  'application/pdf',
  'application/x-python', 'application/x-typescript', 'text/jsx', 'text/tsx',
]);

export function validateAttachmentsForSend(
  attachments: ChatAttachment[]
): { valid: boolean; error?: string } {
  if (attachments.length === 0) return { valid: true };

  let totalSize = 0;
  for (const att of attachments) {
    if (att.size > MAX_FILE_SIZE) {
      return { valid: false, error: `File "${att.name}" exceeds 10MB limit` };
    }
    totalSize += att.size;
  }

  if (totalSize > MAX_TOTAL_SIZE) {
    return {
      valid: false,
      error: `Total attachments exceed 25MB limit (${(totalSize / 1024 / 1024).toFixed(1)}MB)`,
    };
  }

  return { valid: true };
}
