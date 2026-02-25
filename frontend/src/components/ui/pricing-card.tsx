"use client"

import { Check, ArrowRight, Zap } from "lucide-react"
import NumberFlow from "@number-flow/react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export interface PricingTier {
  name: string
  price: Record<string, number | string>
  description: string
  features: string[]
  cta: string
  highlighted?: boolean
  popular?: boolean
}

interface PricingCardProps {
  tier: PricingTier
  paymentFrequency: string
}

export function PricingCard({ tier, paymentFrequency }: PricingCardProps) {
  const price = tier.price[paymentFrequency]
  const isHighlighted = tier.highlighted
  const isPopular = tier.popular
  const trend = paymentFrequency === "yearly" ? -1 : 1

  return (
    <div
      className={cn(
        "relative flex flex-col gap-6 overflow-hidden rounded-2xl border p-6 transition-all duration-300",
        "backdrop-blur-xl",
        isHighlighted
          ? "border-violet-500/40 bg-gradient-to-b from-violet-950/60 to-indigo-950/60 shadow-[0_0_40px_-4px_rgba(139,92,246,0.4)]"
          : isPopular
            ? "border-indigo-500/30 bg-gradient-to-b from-gray-900/70 to-gray-900/50 shadow-[0_0_30px_-4px_rgba(99,102,241,0.25)]"
            : "border-white/5 bg-white/3 hover:border-white/10 hover:bg-white/5"
      )}
    >
      {/* Ambient top glow */}
      {isHighlighted && (
        <div className="pointer-events-none absolute -top-20 left-0 right-0 h-40 bg-[radial-gradient(ellipse_at_top,rgba(139,92,246,0.25),transparent_70%)]" />
      )}
      {isPopular && (
        <div className="pointer-events-none absolute -top-16 left-0 right-0 h-32 bg-[radial-gradient(ellipse_at_top,rgba(99,102,241,0.15),transparent_70%)]" />
      )}

      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <span
            className={cn(
              "text-xs font-semibold uppercase tracking-widest",
              isHighlighted
                ? "text-violet-300"
                : isPopular
                  ? "text-indigo-400"
                  : "text-muted-foreground"
            )}
          >
            {tier.name}
          </span>
          {isPopular && (
            <span className="flex items-center gap-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-300">
              <Zap className="h-3 w-3 fill-current" />
              Most Popular
            </span>
          )}
          {isHighlighted && (
            <span className="rounded-full border border-violet-500/30 bg-violet-500/10 px-2.5 py-0.5 text-xs font-semibold text-violet-300">
              Custom
            </span>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{tier.description}</p>
      </div>

      {/* Price */}
      <div className="flex items-end gap-1">
        {typeof price === "number" ? (
          <>
            <NumberFlow
              format={{ style: "currency", currency: "USD", maximumFractionDigits: 0 }}
              value={price}
              trend={trend}
              className={cn(
                "text-5xl font-bold tracking-tight",
                isHighlighted ? "text-white" : "text-foreground"
              )}
            />
            <span className="mb-1.5 text-sm text-muted-foreground">/mo</span>
          </>
        ) : (
          <span
            className={cn(
              "text-5xl font-bold tracking-tight",
              isHighlighted ? "text-white" : "text-foreground"
            )}
          >
            {price}
          </span>
        )}
      </div>

      {/* Divider */}
      <div
        className={cn(
          "h-px w-full",
          isHighlighted ? "bg-violet-500/20" : "bg-white/5"
        )}
      />

      {/* Features */}
      <ul className="flex-1 space-y-3">
        {tier.features.map((feature, index) => (
          <li key={index} className="flex items-start gap-3 text-sm">
            <span
              className={cn(
                "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full",
                isHighlighted
                  ? "bg-violet-500/20 text-violet-300"
                  : isPopular
                    ? "bg-indigo-500/20 text-indigo-400"
                    : "bg-white/5 text-muted-foreground"
              )}
            >
              <Check className="h-2.5 w-2.5 stroke-[3]" />
            </span>
            <span
              className={cn(
                isHighlighted ? "text-violet-100/90" : "text-muted-foreground"
              )}
            >
              {feature}
            </span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <Button
        className={cn(
          "w-full cursor-pointer font-semibold transition-all duration-200",
          isHighlighted
            ? "bg-violet-500 text-white hover:bg-violet-400 shadow-[0_0_20px_rgba(139,92,246,0.4)]"
            : isPopular
              ? "bg-indigo-600 text-white hover:bg-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.3)]"
              : "border border-white/10 bg-white/5 text-foreground hover:bg-white/10"
        )}
        variant="ghost"
      >
        {tier.cta}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  )
}
