"use client"

import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

interface TabProps {
  text: string
  selected: boolean
  setSelected: (text: string) => void
  discount?: boolean
}

export function Tab({
  text,
  selected,
  setSelected,
  discount = false,
}: TabProps) {
  return (
    <button
      onClick={() => setSelected(text)}
      className={cn(
        "relative z-10 flex cursor-pointer items-center justify-center gap-2 px-5 py-2 text-sm font-semibold capitalize transition-colors duration-200",
        selected ? "text-white" : "text-muted-foreground hover:text-foreground"
      )}
    >
      <span className="relative z-10">{text}</span>

      {discount && (
        <span
          className={cn(
            "relative z-10 rounded-full px-2 py-0.5 text-xs font-bold transition-colors duration-200",
            selected
              ? "bg-indigo-500/30 text-indigo-200"
              : "bg-white/5 text-muted-foreground"
          )}
        >
          −20%
        </span>
      )}

      <AnimatePresence>
        {selected && (
          <motion.span
            layoutId="pricing-tab-pill"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 35 }}
            className="absolute inset-0 -z-0 rounded-full bg-white/10 shadow-inner ring-1 ring-white/10"
          />
        )}
      </AnimatePresence>
    </button>
  )
}
