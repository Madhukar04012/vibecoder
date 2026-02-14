/**
 * AccountHoverPanel - Atmos-style account dropdown overlay
 * Appears on hover from TopBar icon
 */

import { Settings, CreditCard, LogOut } from 'lucide-react';

export default function AccountHoverPanel() {
    return (
        <div
            className="absolute left-0 top-12 w-72 z-50 rounded-xl shadow-2xl shadow-black/50 p-4 animate-in fade-in slide-in-from-top-2 duration-150"
            style={{
                background: 'var(--ide-menu-bg)',
                border: '1px solid var(--ide-menu-border)',
            }}
        >
            {/* USER INFO */}
            <div className="flex items-center gap-3 pb-3" style={{ borderBottom: '1px solid var(--ide-menu-border)' }}>
                <div className="w-11 h-11 rounded-full bg-gradient-to-br from-violet-600 to-purple-700 flex items-center justify-center text-white font-medium text-lg">
                    A
                </div>
                <div className="flex-1">
                    <p className="text-sm font-medium" style={{ color: 'var(--ide-text)' }}>Annam Madhukar Reddy</p>
                    <p className="text-xs" style={{ color: 'var(--ide-text-muted)' }}>Free Plan</p>
                </div>
            </div>

            {/* CREDITS */}
            <div className="mt-3 p-3 rounded-lg" style={{ background: 'var(--ide-credit-bg)' }}>
                <div className="flex items-center justify-between text-xs mb-1.5" style={{ color: 'var(--ide-text-secondary)' }}>
                    <span>Credits remaining</span>
                    <span className="text-red-500 font-medium">0 left</span>
                </div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--ide-progress-track)' }}>
                    <div
                        className="h-full bg-gradient-to-r from-red-500 to-red-600 rounded-full"
                        style={{ width: '0%' }}
                    />
                </div>
            </div>

            {/* ACTIONS */}
            <div className="mt-3 space-y-0.5">
                <MenuButton icon={<CreditCard size={16} />} label="Billing" />
                <MenuButton icon={<Settings size={16} />} label="Settings" />
                <MenuButton icon={<LogOut size={16} />} label="Logout" danger />
            </div>

            {/* UPGRADE */}
            <button className="mt-3 w-full py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 text-white text-sm font-medium hover:from-blue-500 hover:to-blue-600 transition-all shadow-lg shadow-blue-500/20">
                Upgrade to Pro
            </button>
        </div>
    );
}

function MenuButton({
    icon,
    label,
    danger
}: {
    icon: React.ReactNode;
    label: string;
    danger?: boolean;
}) {
    return (
        <button
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
            style={{
                color: danger ? '#f87171' : 'var(--ide-text-secondary)',
            }}
            onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.background = danger ? 'rgba(239,68,68,0.1)' : 'var(--ide-settings-item-hover)';
                if (!danger) (e.currentTarget as HTMLElement).style.color = 'var(--ide-text)';
            }}
            onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.background = 'transparent';
                if (!danger) (e.currentTarget as HTMLElement).style.color = 'var(--ide-text-secondary)';
            }}
        >
            {icon}
            {label}
        </button>
    );
}
