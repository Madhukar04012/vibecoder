import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTheme } from '@/contexts/ThemeContext';

interface NavItem {
  name: string;
  url: string;
  icon: LucideIcon;
}

interface NavBarProps {
  items: NavItem[];
  className?: string;
  defaultActive?: string;
}

export function AnimeNavBar({ items, className, defaultActive = 'Home' }: NavBarProps) {
  const [activeTab, setActiveTab] = useState(defaultActive);
  const { theme } = useTheme();
  const isScrollingToSection = useRef(false);

  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '-50% 0px -50% 0px', // Detect when middle of section is in view
      threshold: 0,
    };

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      if (isScrollingToSection.current) return;

      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const item = items.find((i) => i.url === `#${entry.target.id}`);
          if (item) {
            setActiveTab(item.name);
          }
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);

    items.forEach((item) => {
      if (item.url.startsWith('#')) {
        const el = document.querySelector(item.url);
        if (el) observer.observe(el);
      }
    });

    return () => observer.disconnect();
  }, [items]);

  return (
    <div
      className={cn(
        'fixed bottom-0 sm:top-0 left-1/2 -translate-x-1/2 z-50 mb-6 sm:pt-6',
        className,
      )}
    >
      <div
        className={cn(
          'flex items-center gap-3 border backdrop-blur-xl py-1 px-1 rounded-full shadow-xl',
          theme === 'dark'
            ? 'bg-white/[0.04] border-white/[0.1] shadow-black/20'
            : 'bg-white/60 border-black/[0.06] shadow-black/5',
        )}
      >
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.name;

          return (
            <a
              key={item.name}
              href={item.url}
              onClick={(e) => {
                e.preventDefault();
                setActiveTab(item.name);
                const hash = item.url;
                if (hash.startsWith('#')) {
                  const el = document.querySelector(hash);
                  if (el) {
                    isScrollingToSection.current = true;
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' });

                    // Reset scrolling flag after animation
                    setTimeout(() => {
                      isScrollingToSection.current = false;
                    }, 800);
                  }
                }
              }}
              className={cn(
                'relative cursor-pointer text-sm font-semibold px-6 py-2 rounded-full transition-colors',
                theme === 'dark'
                  ? 'text-white/70 hover:text-white'
                  : 'text-neutral-600 hover:text-neutral-900',
                isActive && (theme === 'dark'
                  ? 'bg-white/[0.06] text-white'
                  : 'bg-black/[0.04] text-neutral-900'),
              )}
            >
              <span className="hidden md:inline">{item.name}</span>
              <span className="md:hidden">
                <Icon size={18} strokeWidth={2.5} />
              </span>
              {isActive && (
                <motion.div
                  layoutId="lamp"
                  className="absolute inset-0 w-full rounded-full -z-10"
                  initial={false}
                  transition={{
                    type: 'spring',
                    stiffness: 300,
                    damping: 30,
                  }}
                >
                  <div
                    className={cn(
                      'absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-1 rounded-t-full',
                      theme === 'dark' ? 'bg-white' : 'bg-neutral-800',
                    )}
                  >
                    <div
                      className={cn(
                        'absolute w-12 h-6 rounded-full blur-md -top-2 -left-2',
                        theme === 'dark' ? 'bg-white/20' : 'bg-neutral-800/15',
                      )}
                    />
                    <div
                      className={cn(
                        'absolute w-8 h-6 rounded-full blur-md -top-1',
                        theme === 'dark' ? 'bg-white/20' : 'bg-neutral-800/15',
                      )}
                    />
                    <div
                      className={cn(
                        'absolute w-4 h-4 rounded-full blur-sm top-0 left-2',
                        theme === 'dark' ? 'bg-white/20' : 'bg-neutral-800/10',
                      )}
                    />
                  </div>
                </motion.div>
              )}
            </a>
          );
        })}
      </div>
    </div>
  );
}
