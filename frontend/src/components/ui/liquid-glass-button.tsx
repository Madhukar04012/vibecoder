import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const liquidbuttonVariants = cva(
  [
    'inline-flex items-center justify-center cursor-pointer gap-2 whitespace-nowrap',
    'font-medium text-sm',
    'transition-[color,box-shadow,transform,filter] duration-300',
    'disabled:pointer-events-none disabled:opacity-50',
    'outline-none focus-visible:ring-2 focus-visible:ring-blue-500/30 dark:focus-visible:ring-blue-300/20',
    'rounded-full',
  ].join(' '),
  {
    variants: {
      variant: {
        default: 'text-gray-900 dark:text-gray-100',
      },
      size: {
        default: 'h-12 px-10',
        sm: 'h-10 px-6 text-xs',
        lg: 'h-14 px-12',
        icon: 'size-12 px-0',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export type LiquidButtonProps = React.ComponentProps<'button'> &
  VariantProps<typeof liquidbuttonVariants> & {
    asChild?: boolean;
  };

export function LiquidButton({
  className,
  variant,
  size,
  asChild = false,
  children,
  ...props
}: LiquidButtonProps) {
  const Comp = asChild ? Slot : 'button';

  return (
    <Comp data-slot="liquid-button" className={cn('relative', liquidbuttonVariants({ variant, size, className }))} {...props}>
      <div
        aria-hidden="true"
        className={cn(
          'absolute inset-0 z-0 rounded-full transition-all',
          // "liquid glass" style shadow stack (light + dark variants)
          'shadow-[0_0_6px_rgba(0,0,0,0.03),0_2px_6px_rgba(0,0,0,0.08),inset_3px_3px_0.5px_-3px_rgba(0,0,0,0.9),inset_-3px_-3px_0.5px_-3px_rgba(0,0,0,0.85),inset_1px_1px_1px_-0.5px_rgba(0,0,0,0.6),inset_-1px_-1px_1px_-0.5px_rgba(0,0,0,0.6),inset_0_0_6px_6px_rgba(0,0,0,0.12),inset_0_0_2px_2px_rgba(0,0,0,0.06),0_0_12px_rgba(255,255,255,0.15)]',
          'dark:shadow-[0_0_8px_rgba(0,0,0,0.03),0_2px_6px_rgba(0,0,0,0.08),inset_3px_3px_0.5px_-3.5px_rgba(255,255,255,0.09),inset_-3px_-3px_0.5px_-3.5px_rgba(255,255,255,0.85),inset_1px_1px_1px_-0.5px_rgba(255,255,255,0.6),inset_-1px_-1px_1px_-0.5px_rgba(255,255,255,0.6),inset_0_0_6px_6px_rgba(255,255,255,0.12),inset_0_0_2px_2px_rgba(255,255,255,0.06),0_0_12px_rgba(0,0,0,0.15)]'
        )}
      />

      <div
        aria-hidden="true"
        className="absolute inset-0 isolate -z-10 overflow-hidden rounded-full bg-white/40 backdrop-blur-xl dark:bg-white/10"
        style={{ backdropFilter: 'url("#container-glass")' }}
      />

      <span className="relative z-10">{children}</span>
      <GlassFilter />
    </Comp>
  );
}

function GlassFilter() {
  return (
    <svg className="hidden" aria-hidden="true">
      <defs>
        <filter id="container-glass" x="0%" y="0%" width="100%" height="100%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0.05 0.05" numOctaves="1" seed="1" result="turbulence" />
          <feGaussianBlur in="turbulence" stdDeviation="2" result="blurredNoise" />
          <feDisplacementMap
            in="SourceGraphic"
            in2="blurredNoise"
            scale="70"
            xChannelSelector="R"
            yChannelSelector="B"
            result="displaced"
          />
          <feGaussianBlur in="displaced" stdDeviation="4" result="finalBlur" />
          <feComposite in="finalBlur" in2="finalBlur" operator="over" />
        </filter>
      </defs>
    </svg>
  );
}

export { liquidbuttonVariants };
