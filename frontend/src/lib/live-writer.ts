/**
 * LiveWriter — Typewriter engine for AI code generation
 *
 * Buffers incoming deltas and drains them character-by-character
 * at a controlled speed to create a smooth "live coding" effect.
 *
 * Speed: ~400 chars/sec per file (adjustable via CHARS_PER_TICK / TICK_MS).
 */

type FlushFn = (path: string, chunk: string) => void;

// ── Speed tuning ─────────────────────────────────────────────────────────────
// CHARS_PER_TICK dripped per animation frame (~60fps = 16ms)
// 48 × 60 = ~2880 chars/sec  →  ~0.35s for a 1 000-char file
// Fewer, larger Zustand updates = less React re-render pressure
const CHARS_PER_TICK = 48;

class LiveWriterEngine {
  /** Pending text per file path */
  private buffers = new Map<string, string>();
  /** RAF handle */
  private rafId: number | null = null;
  /** Callback that actually writes into the Zustand store */
  private onFlush: FlushFn | null = null;

  // ── Public API ──────────────────────────────────────────────────────────

  /** Register the callback that appends content to the store. Pass null to clear. */
  setFlushCallback(cb: FlushFn | null): void {
    this.onFlush = cb;
  }

  /** Push a new delta into the buffer for a file */
  push(path: string, delta: string): void {
    if (!delta) return;
    const existing = this.buffers.get(path) ?? '';
    this.buffers.set(path, existing + delta);
    this.ensureRunning();
  }

  /** Immediately flush all buffered content for one (or every) file */
  flush(path?: string): void {
    if (path) {
      this.drainFile(path);
    } else {
      for (const p of Array.from(this.buffers.keys())) {
        this.drainFile(p);
      }
    }
    if (this.buffers.size === 0) this.stop();
  }

  /** Discard buffer for a file without writing */
  clear(path: string): void {
    this.buffers.delete(path);
    if (this.buffers.size === 0) this.stop();
  }

  /** Hard reset — discard everything, stop timer */
  reset(): void {
    this.buffers.clear();
    this.stop();
  }

  /** Whether a file still has buffered content being drained */
  isPending(path: string): boolean {
    return (this.buffers.get(path)?.length ?? 0) > 0;
  }

  // ── Internals ───────────────────────────────────────────────────────────

  private ensureRunning(): void {
    if (this.rafId !== null) return;
    this.rafId = requestAnimationFrame(() => this.loop());
  }

  private loop(): void {
    this.rafId = null;
    this.tick();
    if (this.buffers.size > 0) {
      this.rafId = requestAnimationFrame(() => this.loop());
    }
  }

  private stop(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  private tick(): void {
    if (!this.onFlush || this.buffers.size === 0) {
      return;
    }

    for (const [path, buf] of this.buffers) {
      if (!buf) {
        this.buffers.delete(path);
        continue;
      }

      // Adaptive drip speed: scale up for large buffers to avoid long drains
      // Base: 48 chars/tick. For buffers > 5k, increase proportionally.
      const adaptiveChars = buf.length > 5000
        ? Math.min(buf.length, Math.max(CHARS_PER_TICK, Math.ceil(buf.length / 60)))
        : Math.min(CHARS_PER_TICK, buf.length);

      // Drain adaptiveChars characters
      const chunk = buf.slice(0, adaptiveChars);
      const rest = buf.slice(adaptiveChars);

      this.onFlush(path, chunk);

      if (rest) {
        this.buffers.set(path, rest);
      } else {
        this.buffers.delete(path);
      }
    }
  }

  /** Flush an entire file buffer at once */
  private drainFile(path: string): void {
    const buf = this.buffers.get(path);
    if (buf && this.onFlush) {
      this.onFlush(path, buf);
    }
    this.buffers.delete(path);
  }
}

/** Singleton — shared across the app */
export const liveWriter = new LiveWriterEngine();
