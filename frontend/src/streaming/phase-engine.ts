/**
 * Phase Engine — Defines the six canonical execution phases.
 *
 * Each backend run passes through these phases in order.
 * The PhaseBlock component reads from the store and renders the current phase.
 */

export type Phase =
  | 'understanding'
  | 'planning'
  | 'architecture'
  | 'implementation'
  | 'validation'
  | 'completed';

export const PHASE_ORDER: Phase[] = [
  'understanding',
  'planning',
  'architecture',
  'implementation',
  'validation',
  'completed',
];

export const PHASE_LABELS: Record<Phase, string> = {
  understanding:  'Understanding',
  planning:       'Planning',
  architecture:   'Architecture',
  implementation: 'Implementation',
  validation:     'Validation',
  completed:      'Completed',
};

/** Accent color per phase */
export const PHASE_COLORS: Record<Phase, string> = {
  understanding:  '#818cf8',
  planning:       '#a78bfa',
  architecture:   '#38bdf8',
  implementation: '#34d399',
  validation:     '#fb7185',
  completed:      '#34d399',
};

/** Baseline progress value when a phase starts */
export const PHASE_PROGRESS: Record<Phase, number> = {
  understanding:  0.03,
  planning:       0.12,
  architecture:   0.28,
  implementation: 0.45,
  validation:     0.80,
  completed:      1.0,
};
