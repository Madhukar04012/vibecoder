/**
 * Phase 4: Diff Format — Canonical internal schema
 * AI can output unified diff or search/replace; we normalize to DiffAction[].
 *
 * Phase 4 invariants:
 * - AI never overwrites files directly
 * - All file modifications are expressed as DiffAction[]
 * - Diffs are previewed and approved before application
 * - Diff application is isolated from executeApprovedPlan
 */

// ─── Canonical Internal Format ─────────────────────────────────────────────────

export type DiffAction =
  | {
      type: 'replace';
      file: string;
      search: string;
      replace: string;
    }
  | {
      type: 'insert';
      file: string;
      after: string;
      content: string;
    }
  | {
      type: 'delete';
      file: string;
      search: string;
    };

export interface DiffPlan {
  summary: string;
  diffs: DiffAction[];
}

// ─── External Formats (AI output) ───────────────────────────────────────────

/** Search/replace block (Cursor-style) */
export interface SearchReplaceBlock {
  file: string;
  search: string;
  replace: string;
}

/** Raw AI output: array of search/replace blocks */
export interface SearchReplaceInput {
  blocks: SearchReplaceBlock[];
}

// ─── Normalization Rules ────────────────────────────────────────────────────

/** Normalize search/replace blocks → DiffAction[] */
export function normalizeSearchReplace(input: SearchReplaceInput): DiffAction[] {
  const diffs: DiffAction[] = [];
  for (const block of input.blocks ?? []) {
    const file = String(block?.file ?? '').trim();
    if (!file) continue;
    const search = String(block?.search ?? '');
    const replace = String(block?.replace ?? '');
    if (replace === '') {
      diffs.push({ type: 'delete', file, search });
    } else {
      diffs.push({ type: 'replace', file, search, replace });
    }
  }
  return diffs;
}

/** Normalize unified diff string → DiffAction[] */
export function normalizeUnifiedDiff(unifiedDiff: string): DiffAction[] {
  const diffs: DiffAction[] = [];
  const lines = unifiedDiff.split('\n');
  let currentFile = '';
  let currentHunk: { before: string[]; after: string[] } = { before: [], after: [] };
  let inHunk = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith('--- ') || line.startsWith('+++ ')) {
      const match = line.match(/^[+-]{3}\s+[ab]\/(.+)$/);
      if (match) currentFile = match[1].trim();
      continue;
    }
    if (line.startsWith('@@ ')) {
      if (inHunk && currentFile && (currentHunk.before.length > 0 || currentHunk.after.length > 0)) {
        const search = currentHunk.before.join('\n');
        const replace = currentHunk.after.join('\n');
        if (search) {
          diffs.push(replace ? { type: 'replace', file: currentFile, search, replace } : { type: 'delete', file: currentFile, search });
        } else if (replace) {
          diffs.push({ type: 'insert', file: currentFile, after: '', content: replace });
        }
      }
      currentHunk = { before: [], after: [] };
      inHunk = true;
      continue;
    }
    if (inHunk && currentFile) {
      if (line.startsWith('-') && !line.startsWith('---')) {
        currentHunk.before.push(line.slice(1));
      } else if (line.startsWith('+') && !line.startsWith('+++')) {
        currentHunk.after.push(line.slice(1));
      } else if (line.startsWith(' ')) {
        const content = line.slice(1);
        currentHunk.before.push(content);
        currentHunk.after.push(content);
      }
    }
  }

  if (inHunk && currentFile && (currentHunk.before.length > 0 || currentHunk.after.length > 0)) {
    const search = currentHunk.before.join('\n');
    const replace = currentHunk.after.join('\n');
    if (search) {
      diffs.push(replace ? { type: 'replace', file: currentFile, search, replace } : { type: 'delete', file: currentFile, search });
    } else if (replace) {
      diffs.push({ type: 'insert', file: currentFile, after: '', content: replace });
    }
  }

  return diffs;
}

/** Normalize any external input → DiffPlan. Safe fallback. */
export function normalizeToDiffPlan(
  input: unknown,
  summaryFallback = 'AI-generated edits'
): DiffPlan {
  if (!input || typeof input !== 'object') {
    return { summary: summaryFallback, diffs: [] };
  }
  const o = input as Record<string, unknown>;

  if (typeof o.diffs === 'object' && Array.isArray(o.diffs)) {
    const diffs = (o.diffs as unknown[]).filter(isValidDiffAction);
    return {
      summary: String(o.summary ?? summaryFallback).slice(0, 500),
      diffs,
    };
  }

  if (o.blocks && Array.isArray(o.blocks)) {
    const diffs = normalizeSearchReplace({ blocks: o.blocks as SearchReplaceBlock[] });
    return {
      summary: String(o.summary ?? summaryFallback).slice(0, 500),
      diffs,
    };
  }

  if (typeof o.unified === 'string') {
    const diffs = normalizeUnifiedDiff(o.unified);
    return {
      summary: String(o.summary ?? summaryFallback).slice(0, 500),
      diffs,
    };
  }

  return { summary: summaryFallback, diffs: [] };
}

/**
 * Phase 4.3: Apply DiffAction[] in memory to produce preview. No filesystem writes.
 * Uses exact string matching; Phase 4.4 handles fuzzy/safety.
 */
export function applyDiffActionsInMemory(
  original: string,
  diffs: DiffAction[],
  filePath: string
): string {
  const fileDiffs = diffs.filter((d) => d.file === filePath || d.file.endsWith(filePath));
  let result = original;
  for (const d of fileDiffs) {
    if (d.type === 'replace' && d.search !== undefined && d.replace !== undefined) {
      const idx = result.indexOf(d.search);
      if (idx >= 0) result = result.slice(0, idx) + d.replace + result.slice(idx + d.search.length);
    } else if (d.type === 'insert' && d.after !== undefined && d.content !== undefined) {
      const idx = d.after === '' ? 0 : result.indexOf(d.after);
      if (idx >= 0) {
        const insertAt = d.after === '' ? 0 : idx + d.after.length;
        result = result.slice(0, insertAt) + d.content + result.slice(insertAt);
      }
    } else if (d.type === 'delete' && d.search !== undefined) {
      const idx = result.indexOf(d.search);
      if (idx >= 0) result = result.slice(0, idx) + result.slice(idx + d.search.length);
    }
  }
  return result;
}

const FUZZY_THRESHOLD = 0.9;

function normalizeWhitespace(s: string): string {
  return s.replace(/\s+/g, ' ').trim();
}

/** Sliding-window similarity: best match position and confidence. Fails if multiple matches. */
function fuzzyFind(content: string, search: string): { index: number; confidence: number } | null {
  if (search.length === 0) return null;
  if (search.length > content.length) return null;

  const normSearch = normalizeWhitespace(search);
  const matches: { index: number; confidence: number }[] = [];

  for (let i = 0; i <= content.length - search.length; i++) {
    const window = content.slice(i, i + search.length);
    const sim = similarity(normalizeWhitespace(window), normSearch);
    if (sim >= FUZZY_THRESHOLD) matches.push({ index: i, confidence: sim });
  }

  if (matches.length === 0) return null;
  if (matches.length > 1) return null; // Ambiguous — fail safely

  const best = matches.reduce((a, b) => (a.confidence >= b.confidence ? a : b));
  return best;
}

function similarity(a: string, b: string): number {
  if (a.length === 0 && b.length === 0) return 1;
  if (a.length === 0 || b.length === 0) return 0;
  let matches = 0;
  const len = Math.min(a.length, b.length);
  for (let i = 0; i < len; i++) {
    if (a[i] === b[i]) matches++;
  }
  return matches / Math.max(a.length, b.length);
}

/**
 * Phase 4.4: Apply a single diff to content. Returns new content or throws.
 * Tries exact match first, then fuzzy. Fails if multiple matches or low confidence.
 */
export function applyDiffActionToContent(
  content: string,
  diff: DiffAction
): string {
  if (diff.type === 'replace' && diff.search !== undefined && diff.replace !== undefined) {
    const exactIdx = content.indexOf(diff.search);
    if (exactIdx >= 0) {
      const count = (content.match(new RegExp(escapeRegex(diff.search), 'g')) ?? []).length;
      if (count > 1) throw new Error(`Multiple exact matches for search in ${diff.file}`);
      return content.slice(0, exactIdx) + diff.replace + content.slice(exactIdx + diff.search.length);
    }
    const fuzzy = fuzzyFind(content, diff.search);
    if (!fuzzy) throw new Error(`No match found for search in ${diff.file}`);
    const chunk = content.slice(fuzzy.index, fuzzy.index + diff.search.length);
    return content.slice(0, fuzzy.index) + diff.replace + content.slice(fuzzy.index + chunk.length);
  }
  if (diff.type === 'insert' && diff.after !== undefined && diff.content !== undefined) {
    const search = diff.after;
    if (search === '') {
      return diff.content + content;
    }
    const exactIdx = content.indexOf(search);
    if (exactIdx >= 0) {
      const count = (content.match(new RegExp(escapeRegex(search), 'g')) ?? []).length;
      if (count > 1) throw new Error(`Multiple exact matches for insert anchor in ${diff.file}`);
      const insertAt = exactIdx + search.length;
      return content.slice(0, insertAt) + diff.content + content.slice(insertAt);
    }
    const fuzzy = fuzzyFind(content, search);
    if (!fuzzy) throw new Error(`No match found for insert anchor in ${diff.file}`);
    const chunk = content.slice(fuzzy.index, fuzzy.index + search.length);
    const insertAt = fuzzy.index + chunk.length;
    return content.slice(0, insertAt) + diff.content + content.slice(insertAt);
  }
  if (diff.type === 'delete' && diff.search !== undefined) {
    const exactIdx = content.indexOf(diff.search);
    if (exactIdx >= 0) {
      const count = (content.match(new RegExp(escapeRegex(diff.search), 'g')) ?? []).length;
      if (count > 1) throw new Error(`Multiple exact matches for delete in ${diff.file}`);
      return content.slice(0, exactIdx) + content.slice(exactIdx + diff.search.length);
    }
    const fuzzy = fuzzyFind(content, diff.search);
    if (!fuzzy) throw new Error(`No match found for delete in ${diff.file}`);
    const chunk = content.slice(fuzzy.index, fuzzy.index + diff.search.length);
    return content.slice(0, fuzzy.index) + content.slice(fuzzy.index + chunk.length);
  }
  throw new Error(`Invalid diff action: ${(diff as { type: string }).type}`);
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function isValidDiffAction(a: unknown): a is DiffAction {
  if (!a || typeof a !== 'object') return false;
  const o = a as Record<string, unknown>;
  const type = o.type as string;
  const file = String(o.file ?? '').trim();
  if (!file) return false;
  if (type === 'replace') {
    return typeof o.search === 'string' && typeof o.replace === 'string';
  }
  if (type === 'insert') {
    return typeof o.after === 'string' && typeof o.content === 'string';
  }
  if (type === 'delete') {
    return typeof o.search === 'string';
  }
  return false;
}
