"use client"

import { useState } from "react";
import { Globe, Sliders, Zap, User, CreditCard, HelpCircle, ExternalLink, Edit, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useSettings } from "@/contexts/SettingsContext";
import { useTheme } from "@/contexts/ThemeContext";

type SettingsTab = 'global-control' | 'domains' | 'integrations' | 'profile' | 'billing' | 'help';

export function SettingsPanel() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('global-control');
  const { language, setLanguage, model, setModel, permissions, setPermissions } = useSettings();
  const { theme, setTheme } = useTheme();

  // Handle sign out
  const handleSignOut = () => {
    try {
      localStorage.removeItem("app-language");
      localStorage.removeItem("app-model");
      localStorage.removeItem("app-permissions");
      localStorage.removeItem("app-theme");
    } catch {
      // Storage unavailable; continue with in-memory reset
    }

    // Reset to defaults
    setLanguage('english');
    setModel('auto');
    setPermissions('public');
    setTheme('dark');

    // Additional sign out logic (e.g. clear auth tokens) can be wired here.

    // Optionally close the dialog or redirect
    window.dispatchEvent(new CustomEvent('user-signed-out'));
  };

  return (
    <div className="flex h-full overflow-hidden" style={{ background: 'var(--ide-settings-bg)' }}>
      {/* Sidebar */}
      <div className="w-[220px] flex flex-col shrink-0" style={{ background: 'var(--ide-settings-sidebar)', borderRight: '1px solid var(--ide-border)' }}>
        <div className="p-4" style={{ borderBottom: '1px solid var(--ide-border)' }}>
          <h3 className="text-[13px] font-semibold" style={{ color: 'var(--ide-text)' }}>Settings</h3>
        </div>

        {/* General Section */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-3 py-4">
            <div className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-3" style={{ color: 'var(--ide-text-faint)' }}>
              General
            </div>
            <button
              onClick={() => setActiveTab('global-control')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
              )}
              style={{
                background: activeTab === 'global-control' ? 'var(--ide-settings-item-active)' : 'transparent',
                color: activeTab === 'global-control' ? 'var(--ide-text)' : 'var(--ide-text-muted)',
                fontWeight: activeTab === 'global-control' ? 500 : 400,
              }}
            >
              <Sliders size={16} />
              Global Control
            </button>
            <button
              onClick={() => setActiveTab('domains')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
              )}
              style={{
                background: activeTab === 'domains' ? 'var(--ide-settings-item-active)' : 'transparent',
                color: activeTab === 'domains' ? 'var(--ide-text)' : 'var(--ide-text-muted)',
                fontWeight: activeTab === 'domains' ? 500 : 400,
              }}
            >
              <Globe size={16} />
              Domains
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
              )}
              style={{
                background: activeTab === 'integrations' ? 'var(--ide-settings-item-active)' : 'transparent',
                color: activeTab === 'integrations' ? 'var(--ide-text)' : 'var(--ide-text-muted)',
                fontWeight: activeTab === 'integrations' ? 500 : 400,
              }}
            >
              <Zap size={16} />
              Integrations
            </button>
          </div>

          {/* Account Section */}
          <div className="px-3 py-4" style={{ borderTop: '1px solid var(--ide-border)' }}>
            <div className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-3" style={{ color: 'var(--ide-text-faint)' }}>
              Account
            </div>
            <button
              onClick={() => setActiveTab('profile')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
              )}
              style={{
                background: activeTab === 'profile' ? 'var(--ide-settings-item-active)' : 'transparent',
                color: activeTab === 'profile' ? 'var(--ide-text)' : 'var(--ide-text-muted)',
                fontWeight: activeTab === 'profile' ? 500 : 400,
              }}
            >
              <User size={16} />
              Profile
            </button>
            <button
              onClick={() => setActiveTab('billing')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
              )}
              style={{
                background: activeTab === 'billing' ? 'var(--ide-settings-item-active)' : 'transparent',
                color: activeTab === 'billing' ? 'var(--ide-text)' : 'var(--ide-text-muted)',
                fontWeight: activeTab === 'billing' ? 500 : 400,
              }}
            >
              <CreditCard size={16} />
              Plans and Billing
            </button>
          </div>

          {/* Support Section */}
          <div className="px-3 py-4" style={{ borderTop: '1px solid var(--ide-border)' }}>
            <div className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-3" style={{ color: 'var(--ide-text-faint)' }}>
              Support
            </div>
            <button
              onClick={() => setActiveTab('help')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
              )}
              style={{
                background: activeTab === 'help' ? 'var(--ide-settings-item-active)' : 'transparent',
                color: activeTab === 'help' ? 'var(--ide-text)' : 'var(--ide-text-muted)',
                fontWeight: activeTab === 'help' ? 500 : 400,
              }}
            >
              <HelpCircle size={16} />
              Help Center
              <ExternalLink size={12} className="ml-auto" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden">
        <div className="p-8 max-w-4xl min-h-full">
          {activeTab === 'global-control' && (
            <>
              <h2 className="text-[20px] font-semibold mb-8" style={{ color: 'var(--ide-text)' }}>Global Control</h2>

              {/* Current Language */}
              <div className="mb-6">
                <h3 className="text-[15px] font-medium mb-4" style={{ color: 'var(--ide-text)' }}>Current Language</h3>
                <p className="text-[12px] mb-3" style={{ color: 'var(--ide-text-faint)' }}>Select the language for the application interface</p>
                <div className="flex items-center justify-between p-4 rounded-lg" style={{ background: 'var(--ide-settings-sidebar)', border: '1px solid var(--ide-border-subtle)' }}>
                  <span className="text-[13px]" style={{ color: 'var(--ide-text-muted)' }}>Language</span>
                  <Select value={language} onValueChange={setLanguage}>
                    <SelectTrigger className="w-[180px]" style={{ background: 'var(--ide-settings-sidebar)', borderColor: 'var(--ide-border)', color: 'var(--ide-text)' }}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent style={{ background: 'var(--ide-settings-sidebar)', borderColor: 'var(--ide-border)' }}>
                      <SelectItem value="english" style={{ color: 'var(--ide-text)' }}>English</SelectItem>
                      <SelectItem value="spanish" style={{ color: 'var(--ide-text)' }}>Spanish</SelectItem>
                      <SelectItem value="french" style={{ color: 'var(--ide-text)' }}>French</SelectItem>
                      <SelectItem value="german" style={{ color: 'var(--ide-text)' }}>German</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Default Model */}
              <div className="mb-6">
                <h3 className="text-[15px] font-medium mb-4" style={{ color: 'var(--ide-text)' }}>Default Model</h3>
                <p className="text-[12px] mb-3" style={{ color: 'var(--ide-text-faint)' }}>Choose the AI model for generating code and responses</p>
                <div className="flex items-center justify-between p-4 rounded-lg" style={{ background: 'var(--ide-settings-sidebar)', border: '1px solid var(--ide-border-subtle)' }}>
                  <span className="text-[13px]" style={{ color: 'var(--ide-text-muted)' }}>Select Model</span>
                  <Select value={model} onValueChange={setModel}>
                    <SelectTrigger className="w-[180px]" style={{ background: 'var(--ide-settings-sidebar)', borderColor: 'var(--ide-border)', color: 'var(--ide-text)' }}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent style={{ background: 'var(--ide-settings-sidebar)', borderColor: 'var(--ide-border)' }}>
                      <SelectItem value="auto" style={{ color: 'var(--ide-text)' }}>Auto</SelectItem>
                      <SelectItem value="minimax-m2.1" style={{ color: 'var(--ide-text)' }}>MiniMax M2.1</SelectItem>
                      <SelectItem value="gpt-4" style={{ color: 'var(--ide-text)' }}>GPT-4</SelectItem>
                      <SelectItem value="gpt-3.5" style={{ color: 'var(--ide-text)' }}>GPT-3.5</SelectItem>
                      <SelectItem value="claude" style={{ color: 'var(--ide-text)' }}>Claude</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Permissions */}
              <div className="mb-6">
                <h3 className="text-[15px] font-medium mb-4" style={{ color: 'var(--ide-text)' }}>Permissions</h3>
                <p className="text-[12px] mb-3" style={{ color: 'var(--ide-text-faint)' }}>Set default visibility for new projects</p>
                <div className="flex items-center justify-between p-4 rounded-lg" style={{ background: 'var(--ide-settings-sidebar)', border: '1px solid var(--ide-border-subtle)' }}>
                  <span className="text-[13px]" style={{ color: 'var(--ide-text-muted)' }}>Set Default Access for Projects</span>
                  <Select value={permissions} onValueChange={setPermissions}>
                    <SelectTrigger className="w-[220px]" style={{ background: 'var(--ide-settings-sidebar)', borderColor: 'var(--ide-border)', color: 'var(--ide-text)' }}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent style={{ background: 'var(--ide-settings-sidebar)', borderColor: 'var(--ide-border)' }}>
                      <SelectItem value="public" style={{ color: 'var(--ide-text)' }}>
                        <div className="flex items-center gap-2">
                          <Globe size={14} />
                          <div>
                            <div className="font-medium">Public</div>
                            <div className="text-[11px]" style={{ color: 'var(--ide-text-faint)' }}>Anyone can view this project</div>
                          </div>
                        </div>
                      </SelectItem>
                      <SelectItem value="private" style={{ color: 'var(--ide-text)' }}>
                        <div className="flex items-center gap-2">
                          <div>
                            <div className="font-medium">Private</div>
                            <div className="text-[11px]" style={{ color: 'var(--ide-text-faint)' }}>Only you can view</div>
                          </div>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Preferences */}
              <div className="mb-6">
                <h3 className="text-[15px] font-medium mb-4" style={{ color: 'var(--ide-text)' }}>Preferences</h3>
                <p className="text-[12px] mb-3" style={{ color: 'var(--ide-text-faint)' }}>Choose your preferred color theme for the application</p>
                <div className="p-4 rounded-lg" style={{ background: 'var(--ide-settings-sidebar)', border: '1px solid var(--ide-border-subtle)' }}>
                  <div className="text-[13px] mb-4" style={{ color: 'var(--ide-text-muted)' }}>Theme</div>
                  <div className="flex gap-4">
                    {/* System Theme */}
                    <button
                      onClick={() => setTheme('system')}
                      className={cn(
                        "flex-1 p-4 rounded-lg border-2 transition-all",
                        theme === 'system'
                          ? "border-blue-500 bg-blue-500/10"
                          : "hover:opacity-80"
                      )}
                      style={{
                        borderColor: theme !== 'system' ? 'var(--ide-border)' : undefined,
                      }}
                    >
                      <div className="w-full aspect-[4/3] rounded-md bg-gradient-to-br from-white via-gray-400 to-black mb-3 overflow-hidden">
                        <div className="w-1/2 h-full bg-white" />
                      </div>
                      <div className="text-[13px] text-center" style={{ color: 'var(--ide-text-secondary)' }}>System</div>
                    </button>

                    {/* Light Theme */}
                    <button
                      onClick={() => setTheme('light')}
                      className={cn(
                        "flex-1 p-4 rounded-lg border-2 transition-all",
                        theme === 'light'
                          ? "border-blue-500 bg-blue-500/10"
                          : "hover:opacity-80"
                      )}
                      style={{
                        borderColor: theme !== 'light' ? 'var(--ide-border)' : undefined,
                      }}
                    >
                      <div className="w-full aspect-[4/3] rounded-md bg-white mb-3" style={{ border: '1px solid var(--ide-border)' }} />
                      <div className="text-[13px] text-center" style={{ color: 'var(--ide-text-secondary)' }}>Light</div>
                    </button>

                    {/* Dark Theme */}
                    <button
                      onClick={() => setTheme('dark')}
                      className={cn(
                        "flex-1 p-4 rounded-lg border-2 transition-all",
                        theme === 'dark'
                          ? "border-blue-500 bg-blue-500/10"
                          : "hover:opacity-80"
                      )}
                      style={{
                        borderColor: theme !== 'dark' ? 'var(--ide-border)' : undefined,
                      }}
                    >
                      <div className="w-full aspect-[4/3] rounded-md bg-[#1a1a1a] mb-3" style={{ border: '1px solid var(--ide-border)' }} />
                      <div className="text-[13px] text-center" style={{ color: 'var(--ide-text-secondary)' }}>Dark</div>
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'domains' && (
            <>
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-[20px] font-semibold" style={{ color: 'var(--ide-text)' }}>Domains</h2>
              </div>

              {/* Coming Soon Message */}
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <h3 className="text-[18px] font-medium mb-2" style={{ color: 'var(--ide-text-secondary)' }}>Coming Soon</h3>
                  <p className="text-[14px]" style={{ color: 'var(--ide-text-muted)' }}>Domain management features will be available soon.</p>
                </div>
              </div>
            </>
          )}

          {activeTab === 'integrations' && (
            <>
              <h2 className="text-[20px] font-semibold mb-8" style={{ color: 'var(--ide-text)' }}>Integrations</h2>

              {/* Coming Soon Message */}
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <h3 className="text-[18px] font-medium mb-2" style={{ color: 'var(--ide-text-secondary)' }}>Coming Soon</h3>
                  <p className="text-[14px]" style={{ color: 'var(--ide-text-muted)' }}>Third-party integration features will be available soon.</p>
                </div>
              </div>
            </>
          )}

          {activeTab === 'profile' && (
            <>
              <h2 className="text-[20px] font-semibold mb-8" style={{ color: 'var(--ide-text)' }}>Profile</h2>

              {/* Avatar */}
              <div className="mb-8">
                <h3 className="text-[15px] font-medium mb-4" style={{ color: 'var(--ide-text)' }}>Avatar</h3>
                <div className="flex items-center justify-end">
                  <Avatar className="h-16 w-16">
                    <AvatarFallback className="bg-blue-600 text-white text-2xl font-bold">
                      A
                    </AvatarFallback>
                  </Avatar>
                </div>
              </div>

              {/* Username */}
              <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--ide-border)' }}>
                <h3 className="text-[15px] font-medium mb-4" style={{ color: 'var(--ide-text)' }}>Username</h3>
                <div className="flex items-center justify-between p-4 rounded-lg" style={{ background: 'var(--ide-settings-sidebar)', border: '1px solid var(--ide-border-subtle)' }}>
                  <span className="text-[14px]" style={{ color: 'var(--ide-text)' }}>Annam Madhukar reddy</span>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Edit size={14} style={{ color: 'var(--ide-text-muted)' }} />
                  </Button>
                </div>
              </div>

              {/* Email */}
              <div className="mb-8 pb-8" style={{ borderBottom: '1px solid var(--ide-border)' }}>
                <h3 className="text-[15px] font-medium mb-4" style={{ color: 'var(--ide-text)' }}>Email</h3>
                <div className="p-4 rounded-lg" style={{ background: 'var(--ide-settings-sidebar)', border: '1px solid var(--ide-border-subtle)' }}>
                  <span className="text-[14px]" style={{ color: 'var(--ide-text)' }}>annammadhukarreddy53@gmail.com</span>
                </div>
              </div>

              {/* Sign Out */}
              <div className="flex justify-end">
                <Button
                  onClick={handleSignOut}
                  className="bg-red-600/20 hover:bg-red-600/30 text-red-400 hover:text-red-300 border border-red-500/30 text-[13px]"
                >
                  <LogOut size={14} className="mr-2" />
                  Sign out
                </Button>
              </div>
            </>
          )}

          {activeTab === 'billing' && (
            <div>
              <h2 className="text-[20px] font-semibold mb-4" style={{ color: 'var(--ide-text)' }}>Plans and Billing</h2>
              <p className="text-[13px]" style={{ color: 'var(--ide-text-muted)' }}>View and manage your subscription</p>
            </div>
          )}

          {activeTab === 'help' && (
            <div>
              <h2 className="text-[20px] font-semibold mb-4" style={{ color: 'var(--ide-text)' }}>Help Center</h2>
              <p className="text-[13px]" style={{ color: 'var(--ide-text-muted)' }}>Get help and support</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
