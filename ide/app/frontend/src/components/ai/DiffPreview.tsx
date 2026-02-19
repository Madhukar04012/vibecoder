import React from 'react';
import { Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAIStore } from '@/stores/aiStore';
import { cn } from '@/lib/utils';

export const DiffPreview: React.FC = () => {
    const pendingDiff = useAIStore((state) => state.pendingDiff);
    const pendingFilePath = useAIStore((state) => state.pendingFilePath);
    const applyDiff = useAIStore((state) => state.applyDiff);
    const rejectDiff = useAIStore((state) => state.rejectDiff);

    if (!pendingDiff || !pendingFilePath) return null;

    return (
        <div className="border-t border-[#3E3E42] bg-[#252526] p-4">
            <div className="mb-3">
                <h3 className="text-[#CCCCCC] text-sm font-medium mb-1">Pending Changes</h3>
                <p className="text-[#858585] text-xs">{pendingFilePath}</p>
            </div>

            <div className="bg-[#1E1E1E] rounded border border-[#3E3E42] p-3 mb-3 max-h-[200px] overflow-y-auto font-mono text-xs">
                {pendingDiff.map((change, index) => (
                    <div
                        key={index}
                        className={cn(
                            'py-0.5',
                            change.type === 'add' && 'text-[#89D185] bg-[#89D185]/10',
                            change.type === 'remove' && 'text-[#F48771] bg-[#F48771]/10',
                            change.type === 'modify' && 'text-[#DDB100] bg-[#DDB100]/10'
                        )}
                    >
                        <span className="text-[#858585] mr-2">{change.lineNumber}</span>
                        {change.type === 'add' && '+ '}
                        {change.type === 'remove' && '- '}
                        {change.type === 'modify' && '~ '}
                        {change.content}
                    </div>
                ))}
            </div>

            <div className="flex gap-2">
                <Button
                    onClick={applyDiff}
                    className="flex-1 bg-[#89D185] hover:bg-[#7BC67C] text-[#1E1E1E] gap-1.5"
                >
                    <Check className="w-4 h-4" />
                    Apply Changes
                </Button>
                <Button
                    onClick={rejectDiff}
                    variant="outline"
                    className="flex-1 border-[#3E3E42] text-[#CCCCCC] hover:bg-[#2A2D2E] gap-1.5"
                >
                    <X className="w-4 h-4" />
                    Reject
                </Button>
            </div>
        </div>
    );
};