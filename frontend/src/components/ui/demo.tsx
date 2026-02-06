import { LiquidButton } from '@/components/ui/liquid-glass-button';

export default function DemoOne() {
  return (
    <div className="flex min-h-[240px] w-full items-center justify-center bg-black px-6">
      <div className="relative h-[200px] w-full max-w-[800px]">
        <LiquidButton className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2">
          Liquid Glass
        </LiquidButton>
      </div>
    </div>
  );
}
