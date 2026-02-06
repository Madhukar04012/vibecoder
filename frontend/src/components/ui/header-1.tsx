import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { MenuToggleIcon } from '@/components/ui/menu-toggle-icon';
import { useScroll } from '@/components/ui/use-scroll';

function WordmarkIcon({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2 text-lg font-semibold tracking-tight text-gray-900', className)}>
      <span>VibeCober</span>
      <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">Local AI</span>
    </span>
  );
}

function useLockBodyScroll(locked: boolean) {
  useEffect(() => {
    if (!locked) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [locked]);
}

export function Header({
  onLogoClick,
  onGetStarted,
  onSignIn,
}: {
  onLogoClick?: () => void;
  onGetStarted?: () => void;
  onSignIn?: () => void;
}) {
  const scrolled = useScroll(10);
  const [open, setOpen] = useState(false);
  const [activeHref, setActiveHref] = useState<string | null>(null);
  useLockBodyScroll(open);

  const links = useMemo(
    () => [
      { label: 'Features', href: '#features' },
      { label: 'Pricing', href: '#pricing' },
      { label: 'About', href: '#faq' },
    ],
    []
  );

  useEffect(() => {
    const ids = links
      .map((l) => l.href)
      .filter((href) => href.startsWith('#'))
      .map((href) => href.slice(1));

    const elements = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => Boolean(el));

    if (elements.length === 0) {
      setActiveHref(null);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => (b.intersectionRatio ?? 0) - (a.intersectionRatio ?? 0));

        const top = visible[0];
        const id = top?.target?.id;
        setActiveHref(id ? `#${id}` : null);
      },
      {
        root: null,
        threshold: [0.1, 0.2, 0.35, 0.5, 0.65],
        rootMargin: '-40% 0px -55% 0px',
      }
    );

    for (const el of elements) observer.observe(el);
    return () => observer.disconnect();
  }, [links]);

  const scrollToHash = (href: string) => {
    if (!href.startsWith('#')) return;
    const id = href.slice(1);

    let attempts = 0;
    const tryScroll = () => {
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setActiveHref(href);
        return;
      }
      attempts += 1;
      if (attempts < 12) requestAnimationFrame(tryScroll);
    };

    requestAnimationFrame(tryScroll);
  };

  const handleNavClick = (href: string) => (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (href.startsWith('#')) {
      e.preventDefault();
      setOpen(false);
      onLogoClick?.();
      scrollToHash(href);
    }
  };

  return (
    <header
      className={cn(
        'fixed top-0 left-0 right-0 z-50',
        'bg-white/80 backdrop-blur-xl',
        scrolled ? 'border-b border-gray-200' : 'border-b border-transparent'
      )}
    >
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center px-6">
        <div className="flex items-center">
          <button
            type="button"
            onClick={onLogoClick}
            className="inline-flex items-center gap-2"
            aria-label="Home"
            title="Home"
          >
            <WordmarkIcon className="text-xl font-semibold" />
          </button>
        </div>

        <nav className="hidden flex-1 items-center justify-center gap-10 text-sm md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={handleNavClick(l.href)}
              aria-current={activeHref === l.href ? 'page' : undefined}
              className={cn(
                'transition-colors',
                activeHref === l.href ? 'text-gray-900' : 'text-gray-600 hover:text-gray-900'
              )}
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <Button
            variant="outline"
            onClick={onSignIn}
            className="h-10 rounded-xl border-gray-300 bg-white px-5 text-gray-900 hover:bg-gray-50"
          >
            Sign In
          </Button>
          <Button onClick={onGetStarted} className="h-10 rounded-xl bg-gray-900 px-5 text-white hover:bg-gray-800">
            Get Started
          </Button>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="md:hidden ml-auto rounded-xl text-gray-900 hover:bg-gray-100"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? 'Close menu' : 'Open menu'}
        >
          <MenuToggleIcon open={open} className="h-5 w-5" />
        </Button>
      </div>

      {open &&
        createPortal(
          <div className="fixed inset-0 z-50 md:hidden">
            <div className="absolute inset-0 bg-black/30" onClick={() => setOpen(false)} />
            <div className="absolute left-0 right-0 top-0 mx-auto mt-20 w-[min(92vw,32rem)] rounded-2xl border border-gray-200 bg-white/95 backdrop-blur-xl p-4">
              <div className="flex flex-col gap-3">
                {links.map((l) => (
                  <a
                    key={l.href}
                    href={l.href}
                    onClick={(e) => {
                      if (l.href.startsWith('#')) {
                        e.preventDefault();
                        setOpen(false);
                        onLogoClick?.();
                        scrollToHash(l.href);
                        return;
                      }
                      setOpen(false);
                    }}
                    className="rounded-xl px-3 py-3 text-gray-800 hover:bg-gray-100 transition-colors"
                  >
                    {l.label}
                  </a>
                ))}

                <div className="h-px w-full bg-gray-200" />

                <Button
                  variant="outline"
                  className="w-full rounded-xl border-gray-300 bg-white text-gray-900 hover:bg-gray-50"
                  onClick={onSignIn}
                >
                  Sign In
                </Button>
                <Button
                  className="w-full rounded-xl bg-gray-900 text-white hover:bg-gray-800"
                  onClick={onGetStarted}
                >
                  Get Started
                </Button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </header>
  );
}
