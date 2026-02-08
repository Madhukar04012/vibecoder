/**
 * Phase 5: Controlled Autonomy — Policy layer
 *
 * Phase 5 invariants:
 * - Autonomy is decided per action, not globally
 * - Auto-approved changes must be fully rollbackable
 * - Any failure disables autonomy for that execution
 * - Users can always opt out
 */

import type { DiffPlan } from './diff';

export interface AutonomyDecision {
  autoApprove: boolean;
  reason: string;
}

/** Paths that require manual review (config, infra, auth) */
const SENSITIVE_PATH_PATTERNS = [
  /\.env/i,
  /config/i,
  /\.config/i,
  /auth/i,
  /\.pem$/i,
  /\.key$/i,
  /dockerfile/i,
  /docker-compose/i,
  /\.github/i,
  /package\.json/i,
  /package-lock/i,
  /yarn\.lock/i,
  /tsconfig/i,
  /vite\.config/i,
];

function isSensitivePath(path: string): boolean {
  const p = path.toLowerCase().replace(/^\/+/, '');
  return SENSITIVE_PATH_PATTERNS.some((pat) => pat.test(p));
}

function countLines(s: string): number {
  if (!s) return 0;
  return (s.match(/\n/g) ?? []).length + 1;
}

/**
 * Phase 5.1: Autonomy Gate — Pure decision logic, no side effects.
 * Auto-approve only when ALL heuristics pass.
 */
export function shouldAutoApprove(diffPlan: DiffPlan): AutonomyDecision {
  const { diffs } = diffPlan;
  if (diffs.length === 0) {
    return { autoApprove: false, reason: 'No diffs' };
  }

  const files = [...new Set(diffs.map((d) => d.file))];
  if (files.length > 1) {
    return { autoApprove: false, reason: 'More than one file affected' };
  }

  for (const path of files) {
    if (isSensitivePath(path)) {
      return { autoApprove: false, reason: `Sensitive path: ${path}` };
    }
  }

  let totalLines = 0;
  for (const d of diffs) {
    if (d.type === 'delete') {
      return { autoApprove: false, reason: 'Delete actions require review' };
    }
    if (d.type === 'replace') {
      return { autoApprove: false, reason: 'Replace actions require review' };
    }
    if (d.type === 'insert' && d.content !== undefined) {
      totalLines += countLines(d.content);
    }
  }

  if (totalLines > 10) {
    return { autoApprove: false, reason: `More than 10 lines changed (${totalLines})` };
  }

  return {
    autoApprove: true,
    reason: 'Low risk: single file, insert only, ≤10 lines',
  };
}
