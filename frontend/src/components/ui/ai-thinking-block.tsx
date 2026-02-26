"use client";

import { Card } from "@/components/ui/card";
import { Loader } from "@/components/ui/loader";
import { useEffect, useRef, useState } from "react";

interface AIThinkingBlockProps {
    /** Live thinking text streamed from the model */
    content?: string;
    /** Label shown next to the spinner (default: "AI is thinking") */
    label?: string;
}

export default function AIThinkingBlock({
    content = "",
    label = "AI is thinking",
}: AIThinkingBlockProps) {
    const contentRef = useRef<HTMLDivElement>(null);
    const [timer, setTimer] = useState(0);

    // Elapsed-time counter
    useEffect(() => {
        const timerInterval = setInterval(() => {
            setTimer((prev) => prev + 1);
        }, 1000);
        return () => clearInterval(timerInterval);
    }, []);

    // Auto-scroll to bottom as new content streams in
    useEffect(() => {
        if (contentRef.current) {
            contentRef.current.scrollTop = contentRef.current.scrollHeight;
        }
    }, [content]);

    return (
        <>
            {/* Shimmer keyframe — standard <style>, no styled-jsx */}
            <style>{`
        @keyframes ai-thinking-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>

            <div className="flex flex-col p-3 max-w-xl">
                <div className="flex items-center justify-start gap-2 mb-4">
                    <Loader size={"sm"} />
                    <p
                        className="bg-[linear-gradient(110deg,#404040,35%,#fff,50%,#404040,75%,#404040)] bg-[length:200%_100%] bg-clip-text text-base text-transparent"
                        style={{
                            animation: "ai-thinking-shimmer 5s linear infinite",
                        }}
                    >
                        {label}
                    </p>
                    <span className="text-sm text-muted-foreground">
                        {timer}s
                    </span>
                </div>

                {/* Only show the content card when there is actual thinking text */}
                {content && (
                    <Card className="relative h-[150px] overflow-hidden bg-secondary p-2 rounded-[var(--card-radius,10px)]">
                        {/* Top fade overlay */}
                        <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-30% from-secondary to-transparent z-10 pointer-events-none h-[80px]" />

                        {/* Bottom fade overlay */}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-30% from-secondary to-transparent z-10 pointer-events-none h-[80px]" />

                        {/* Scrolling content — auto-scrolls to bottom as tokens arrive */}
                        <div
                            ref={contentRef}
                            className="h-full overflow-hidden p-4 text-secondary-foreground"
                            style={{ scrollBehavior: "auto" }}
                        >
                            <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                {content}
                            </p>
                        </div>
                    </Card>
                )}
            </div>
        </>
    );
}
