/**
 * Chat InputArea — textarea, attachment display, send/stop/clear controls.
 * Extracted from AtomsChatPanel to keep that file focused on message orchestration.
 */

import { useEffect, useCallback, type KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { Send, RotateCcw, Plus, X, Paperclip, Code2, Upload } from "lucide-react";
import type { ChatAttachment } from "./attachment";

interface InputAreaProps {
  input: string;
  setInput: (v: string) => void;
  isStreaming: boolean;
  attachments: ChatAttachment[];
  chatMessagesCount: number;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  fileInputRef: React.RefObject<HTMLInputElement>;
  onSend: () => void;
  onStop: () => void;
  onClear: () => void;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveAttachment: (id: string) => void;
}

export function InputArea({
  input,
  setInput,
  isStreaming,
  attachments,
  chatMessagesCount,
  textareaRef,
  fileInputRef,
  onSend,
  onStop,
  onClear,
  onFileUpload,
  onRemoveAttachment,
}: InputAreaProps) {
  // Auto-resize textarea as content grows
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [input]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        onSend();
      }
    },
    [onSend]
  );

  return (
    <div style={{
      padding: '12px 16px 14px',
      flexShrink: 0,
      background: 'var(--bg-base)',
      borderTop: '1px solid var(--border-subtle)',
      zIndex: 20,
    }}>
      {/* Attachment badges */}
      {attachments.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachments.map((attachment) => (
            <div
              key={attachment.id}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '6px 12px', borderRadius: 8,
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.14)',
                color: 'var(--text-secondary)', fontSize: 12,
                fontFamily: 'var(--font-ui)',
              }}
              title={`${attachment.name} (${(attachment.size / 1024 / 1024).toFixed(1)}MB)`}
            >
              {attachment.type === 'image' ? (
                <Paperclip size={13} style={{ color: '#60a5fa' }} />
              ) : attachment.type === 'code' ? (
                <Code2 size={13} style={{ color: '#34d399' }} />
              ) : (
                <Upload size={13} style={{ color: '#94a3b8' }} />
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
                <span style={{
                  maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap', fontWeight: 500,
                }}>
                  {attachment.name}
                </span>
                <span style={{ fontSize: 10, opacity: 0.6 }}>
                  {(attachment.size / 1024).toFixed(0)} KB
                </span>
              </div>
              <button
                type="button"
                title="Remove attachment"
                aria-label="Remove attachment"
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-muted)', padding: 2, borderRadius: 4,
                  lineHeight: 0, marginLeft: 'auto', flexShrink: 0,
                }}
                onClick={() => onRemoveAttachment(attachment.id)}
              >
                <X size={13} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input container */}
      <div className={`chat-input-container${isStreaming ? ' streaming' : ''}`}>
        <div style={{ display: 'flex', alignItems: 'flex-end', padding: '8px 10px' }}>
          {/* Attachment button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', padding: '6px', borderRadius: 8,
              lineHeight: 0, flexShrink: 0, marginBottom: 2,
              transition: 'color 0.15s ease',
            }}
            title="Add attachment"
          >
            <Plus size={17} />
          </button>

          <label htmlFor="chat-file-input" className="hidden">Upload attachments</label>
          <input
            id="chat-file-input"
            ref={fileInputRef}
            type="file"
            multiple
            onChange={onFileUpload}
            className="hidden"
            accept=".txt,.py,.js,.ts,.tsx,.jsx,.md,.json,.yaml,.yml,.html,.css,.scss,.png,.jpg,.jpeg,.gif,.svg,.pdf"
          />

          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            style={{
              flex: 1,
              background: 'transparent', border: 'none', outline: 'none',
              resize: 'none', padding: '6px 8px',
              fontSize: 'var(--text-base)',
              lineHeight: 'var(--leading-relaxed)',
              color: 'var(--text-primary)',
              caretColor: 'var(--accent)',
              fontFamily: 'var(--font-ui)',
              minHeight: 36, maxHeight: 150,
              opacity: isStreaming ? 0.5 : 1,
            }}
            placeholder="Describe what you want to build..."
          />

          {/* Send / Stop + Clear controls */}
          <div style={{ flexShrink: 0, marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6 }}>
            {/* Clear — only when there are messages and not streaming */}
            {!isStreaming && chatMessagesCount > 0 && (
              <button
                type="button"
                onClick={onClear}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  padding: '7px 10px', borderRadius: 9,
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: 'rgba(255,255,255,0.32)',
                  cursor: 'pointer', fontSize: 11,
                  fontFamily: 'var(--font-ui)',
                  transition: 'all 0.2s ease', lineHeight: 0,
                }}
                title="Clear conversation"
                onMouseEnter={e => {
                  (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.65)';
                  (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.18)';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.32)';
                  (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.08)';
                }}
              >
                <X size={14} />
              </button>
            )}

            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                style={{
                  display: 'flex', alignItems: 'center', gap: 5,
                  padding: '6px 10px', borderRadius: 8,
                  background: 'rgba(248,113,113,0.10)',
                  border: '1px solid rgba(248,113,113,0.25)',
                  color: '#f87171', fontSize: 12, fontWeight: 600,
                  cursor: 'pointer', fontFamily: 'var(--font-ui)',
                  transition: 'background 0.15s ease',
                }}
              >
                <RotateCcw size={13} />
                Stop
              </button>
            ) : (
              <motion.button
                type="button"
                onClick={onSend}
                disabled={!input.trim()}
                whileHover={input.trim() ? { scale: 1.05 } : {}}
                whileTap={input.trim() ? { scale: 0.93 } : {}}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  padding: '7px 10px', borderRadius: 9,
                  background: input.trim() ? 'var(--accent)' : 'rgba(255,255,255,0.06)',
                  border: '1px solid transparent',
                  color: input.trim() ? 'white' : 'var(--text-dim)',
                  cursor: input.trim() ? 'pointer' : 'not-allowed',
                  opacity: input.trim() ? 1 : 0.5,
                  boxShadow: input.trim() ? '0 0 16px rgba(99,102,241,0.30)' : 'none',
                  transition: 'background 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease',
                  lineHeight: 0,
                }}
                title="Send message"
              >
                <Send size={15} />
              </motion.button>
            )}
          </div>
        </div>

        {/* Keyboard hint */}
        <div style={{
          padding: '6px 14px',
          display: 'flex', alignItems: 'center',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: 11, color: 'var(--text-dim)', fontFamily: 'var(--font-ui)',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <kbd style={{
              padding: '1px 5px', borderRadius: 4,
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid var(--border-default)',
              fontFamily: 'var(--font-mono)', fontSize: 10,
            }}>
              Enter
            </kbd>
            {' '}to send · Shift+Enter for new line
          </span>
        </div>
      </div>
    </div>
  );
}
