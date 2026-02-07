import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-white/10">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <div
              className="h-8 w-8 rounded-lg border border-white/10 bg-white/5"
              aria-hidden="true"
            />
            <span className="text-sm font-semibold tracking-tight">VibeCober</span>
          </div>

          <div className="flex items-center gap-2">
            <Button asChild variant="outline" size="sm">
              <Link href="/ide">Launch IDE</Link>
            </Button>
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 opacity-70" aria-hidden="true">
            <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-violet-500/15 blur-3xl" />
            <div className="absolute -right-24 top-24 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
            <div className="absolute left-1/3 bottom-[-140px] h-96 w-96 rounded-full bg-fuchsia-500/5 blur-3xl" />
          </div>

          <div className="relative mx-auto max-w-6xl px-4 py-16">
            <div className="max-w-2xl">
              <p className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">
                AI team lead + IDE in one workspace
              </p>
              <h1 className="mt-4 text-balance text-4xl font-semibold tracking-tight md:text-5xl">
                Build features end-to-end with VibeCober
              </h1>
              <p className="mt-4 text-sm leading-relaxed text-slate-300 md:text-base">
                Chat with agents, generate plans, edit code, and run tasks — all in a calm, developer-first interface.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="flex w-full max-w-xl items-center gap-2 rounded-xl border border-white/10 bg-white/5 p-2">
                  <Input
                    className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
                    placeholder="Describe what you want to build..."
                    aria-label="Build prompt"
                  />
                  <Button asChild>
                    <Link href="/ide">Get Started</Link>
                  </Button>
                </div>

                <Button asChild variant="secondary">
                  <Link href="/ide-demo">View Demo</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
