import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useAIStore } from '@/stores/aiStore';
import { cn } from '@/lib/utils';

export const AIChatInterface: React.FC = () => {
    const messages = useAIStore((state) => state.messages);
    const addMessage = useAIStore((state) => state.addMessage);
    const isProcessing = useAIStore((state) => state.isProcessing);
    const setProcessing = useAIStore((state) => state.setProcessing);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = () => {
        if (input.trim() && !isProcessing) {
            addMessage({ role: 'user', content: input });
            setInput('');
            setProcessing(true);

            // Simulate AI response
            setTimeout(() => {
                addMessage({
                    role: 'assistant',
                    content: "I understand your request. I'll help you with that code change.",
                    toolCalls: [
                        {
                            id: 'tool-1',
                            name: 'edit_file',
                            status: 'completed',
                            input: { file: '/src/components/App.tsx' },
                            output: 'File updated successfully',
                        },
                    ],
                });
                setProcessing(false);
            }, 1000);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={cn(
                            'flex gap-3',
                            message.role === 'user' ? 'justify-end' : 'justify-start'
                        )}
                    >
                        {message.role !== 'user' && (
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                                <Sparkles className="w-4 h-4 text-white" />
                            </div>
                        )}
                        <div
                            className={cn(
                                'max-w-[80%] rounded-lg p-3 text-sm',
                                message.role === 'user'
                                    ? 'bg-[#007ACC] text-white'
                                    : 'bg-[#2D2D30] text-[#CCCCCC]'
                            )}
                        >
                            <p className="whitespace-pre-wrap">{message.content}</p>
                            {message.toolCalls && message.toolCalls.length > 0 && (
                                <div className="mt-2 space-y-1">
                                    {message.toolCalls.map((tool) => (
                                        <div
                                            key={tool.id}
                                            className="text-xs bg-[#1E1E1E] rounded p-2 border border-[#3E3E42]"
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-[#89D185]">{tool.name}</span>
                                                <span
                                                    className={cn(
                                                        'text-xs',
                                                        tool.status === 'completed' && 'text-[#89D185]',
                                                        tool.status === 'failed' && 'text-[#F48771]',
                                                        tool.status === 'running' && 'text-[#DDB100]'
                                                    )}
                                                >
                                                    {tool.status}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        {message.role === 'user' && (
                            <div className="w-8 h-8 rounded-full bg-[#007ACC] flex items-center justify-center flex-shrink-0">
                                <span className="text-white text-sm font-medium">U</span>
                            </div>
                        )}
                    </div>
                ))}
                {isProcessing && (
                    <div className="flex gap-3 justify-start">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white animate-pulse" />
                        </div>
                        <div className="bg-[#2D2D30] rounded-lg p-3">
                            <div className="flex gap-1">
                                <div className="w-2 h-2 bg-[#858585] rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-[#858585] rounded-full animate-bounce delay-100" />
                                <div className="w-2 h-2 bg-[#858585] rounded-full animate-bounce delay-200" />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-[#3E3E42] p-3">
                <div className="flex gap-2">
                    <Textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask AI to help with your code..."
                        className="flex-1 bg-[#3C3C3C] border-[#3E3E42] text-[#CCCCCC] resize-none"
                        rows={3}
                    />
                    <Button
                        onClick={handleSend}
                        disabled={!input.trim() || isProcessing}
                        className="bg-[#007ACC] hover:bg-[#0098FF] text-white self-end"
                    >
                        <Send className="w-4 h-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
};