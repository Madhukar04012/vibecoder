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
// CHARS_PER_TICK × (1000 / TICK_MS) = chars/sec
// 16 × (1000 / 8) = 2000 chars/sec  →  ~0.5 s for a 1 000-char file
const CHARS_PER_TICK = 16;
const TICK_MS = 8;

class LiveWriterEngine {
  /** Pending text per file path */
  private buffers = new Map<string, string>();
  /** Interval handle */
  private timer: ReturnType<typeof setInterval> | null = null;
  /** Callback that actually writes into the Zustand store */
  private onFlush: FlushFn | null = null;

  // ── Public API ──────────────────────────────────────────────────────────

  /** Register the callback that appends content to the store */
  setFlushCallback(cb: FlushFn): void {
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
    if (this.timer) return;
    this.timer = setInterval(() => this.tick(), TICK_MS);
  }

  private stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  private tick(): void {
    if (!this.onFlush || this.buffers.size === 0) {
      this.stop();
      return;
    }

    for (const [path, buf] of this.buffers) {
      if (!buf) {
        this.buffers.delete(path);
        continue;
      }

      // Drain CHARS_PER_TICK characters
      const chunk = buf.slice(0, CHARS_PER_TICK);
      const rest = buf.slice(CHARS_PER_TICK);

      this.onFlush(path, chunk);

      if (rest) {
        this.buffers.set(path, rest);
      } else {
        this.buffers.delete(path);
      }
    }

    if (this.buffers.size === 0) this.stop();
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
