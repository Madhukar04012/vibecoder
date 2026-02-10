"use client"

import { useState } from "react";
import { Globe, Sliders, Zap, User, CreditCard, HelpCircle, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
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

type SettingsTab = 'global-control' | 'domains' | 'integrations' | 'profile' | 'billing' | 'help';

export function SettingsPanel() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('global-control');
  const { language, setLanguage, model, setModel, permissions, setPermissions, theme, setTheme } = useSettings();

  // Handle sign out
  const handleSignOut = () => {
    // Clear all settings
    localStorage.removeItem('app-language');
    localStorage.removeItem('app-model');
    localStorage.removeItem('app-permissions');
    localStorage.removeItem('app-theme');
    
    // Reset to defaults
    setLanguage('english');
    setModel('auto');
    setPermissions('public');
    setTheme('dark');
    
    // You can add additional sign out logic here (e.g., clear auth tokens, redirect, etc.)
    console.log('User signed out, settings cleared');
    
    // Optionally close the dialog or redirect
    window.dispatchEvent(new CustomEvent('user-signed-out'));
  };

  return (
    <div className="flex h-full bg-[#1a1a1a] overflow-hidden">
      {/* Sidebar */}
      <div className="w-[220px] bg-[#2a2a2a] border-r border-white/10 flex flex-col shrink-0">
        <div className="p-4 border-b border-white/10">
          <h3 className="text-[13px] font-semibold text-white">Settings</h3>
        </div>

        {/* General Section */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-3 py-4">
            <div className="text-[11px] font-semibold text-white/40 uppercase tracking-wider mb-2 px-3">
              General
            </div>
            <button
              onClick={() => setActiveTab('global-control')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
                activeTab === 'global-control'
                  ? "bg-white/10 text-white font-medium"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
              )}
            >
              <Sliders size={16} />
              Global Control
            </button>
            <button
              onClick={() => setActiveTab('domains')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
                activeTab === 'domains'
                  ? "bg-white/10 text-white font-medium"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
              )}
            >
              <Globe size={16} />
              Domains
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
                activeTab === 'integrations'
                  ? "bg-white/10 text-white font-medium"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
              )}
            >
              <Zap size={16} />
              Integrations
            </button>
          </div>

          {/* Account Section */}
          <div className="px-3 py-4 border-t border-white/10">
            <div className="text-[11px] font-semibold text-white/40 uppercase tracking-wider mb-2 px-3">
              Account
            </div>
            <button
              onClick={() => setActiveTab('profile')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
                activeTab === 'profile'
                  ? "bg-white/10 text-white font-medium"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
              )}
            >
              <User size={16} />
              Profile
            </button>
            <button
              onClick={() => setActiveTab('billing')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
                activeTab === 'billing'
                  ? "bg-white/10 text-white font-medium"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
              )}
            >
              <CreditCard size={16} />
              Plans and Billing
            </button>
          </div>

          {/* Support Section */}
          <div className="px-3 py-4 border-t border-white/10">
            <div className="text-[11px] font-semibold text-white/40 uppercase tracking-wider mb-2 px-3">
              Support
            </div>
            <button
              onClick={() => setActiveTab('help')}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-[13px] transition-colors",
                activeTab === 'help'
                  ? "bg-white/10 text-white font-medium"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
              )}
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
              <h2 className="text-[20px] font-semibold text-white mb-8">Global Control</h2>

              {/* Current Language */}
              <div className="mb-6">
                <h3 className="text-[15px] font-medium text-white mb-4">Current Language</h3>
                <p className="text-[12px] text-white/40 mb-3">Select the language for the application interface</p>
                <div className="flex items-center justify-between p-4 rounded-lg bg-[#2a2a2a]/50 border border-white/5">
                  <span className="text-[13px] text-white/60">Language</span>
                  <Select value={language} onValueChange={setLanguage}>
                    <SelectTrigger className="w-[180px] bg-[#2a2a2a] border-white/10 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#2a2a2a] border-white/10">
                      <SelectItem value="english" className="text-white">English</SelectItem>
                      <SelectItem value="spanish" className="text-white">Spanish</SelectItem>
                      <SelectItem value="french" className="text-white">French</SelectItem>
                      <SelectItem value="german" className="text-white">German</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Default Model */}
              <div className="mb-6">
                <h3 className="text-[15px] font-medium text-white mb-4">Default Model</h3>
                <p className="text-[12px] text-white/40 mb-3">Choose the AI model for generating code and responses</p>
                <div className="flex items-center justify-between p-4 rounded-lg bg-[#2a2a2a]/50 border border-white/5">
                  <span className="text-[13px] text-white/60">Select Model</span>
                  <Select value={model} onValueChange={setModel}>
                    <SelectTrigger className="w-[180px] bg-[#2a2a2a] border-white/10 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#2a2a2a] border-white/10">
                      <SelectItem value="auto" className="text-white">Auto</SelectItem>
                      <SelectItem value="gpt-4" className="text-white">GPT-4</SelectItem>
                      <SelectItem value="gpt-3.5" className="text-white">GPT-3.5</SelectItem>
                      <SelectItem value="claude" className="text-white">Claude</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Permissions */}
              <div className="mb-6">
                <h3 className="text-[15px] font-medium text-white mb-4">Permissions</h3>
                <p className="text-[12px] text-white/40 mb-3">Set default visibility for new projects</p>
                <div className="flex items-center justify-between p-4 rounded-lg bg-[#2a2a2a]/50 border border-white/5">
                  <span className="text-[13px] text-white/60">Set Default Access for Projects</span>
                  <Select value={permissions} onValueChange={setPermissions}>
                    <SelectTrigger className="w-[220px] bg-[#2a2a2a] border-white/10 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#2a2a2a] border-white/10">
                      <SelectItem value="public" className="text-white">
                        <div className="flex items-center gap-2">
                          <Globe size={14} />
                          <div>
                            <div className="font-medium">Public</div>
                            <div className="text-[11px] text-white/40">Anyone can view this project</div>
                          </div>
                        </div>
                      </SelectItem>
                      <SelectItem value="private" className="text-white">
                        <div className="flex items-center gap-2">
                          <div>
                            <div className="font-medium">Private</div>
                            <div className="text-[11px] text-white/40">Only you can view</div>
                          </div>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Preferences */}
              <div className="mb-6">
                <h3 className="text-[15px] font-medium text-white mb-4">Preferences</h3>
                <p className="text-[12px] text-white/40 mb-3">Choose your preferred color theme for the application</p>
                <div className="p-4 rounded-lg bg-[#2a2a2a]/50 border border-white/5">
                  <div className="text-[13px] text-white/60 mb-4">Theme</div>
                  <div className="flex gap-4">
                    {/* System Theme */}
                    <button
                      onClick={() => setTheme('system')}
                      className={cn(
                        "flex-1 p-4 rounded-lg border-2 transition-all",
                        theme === 'system'
                          ? "border-blue-500 bg-blue-500/10"
                          : "border-white/10 hover:border-white/20"
                      )}
                    >
                      <div className="w-full aspect-[4/3] rounded-md bg-gradient-to-br from-white via-gray-400 to-black mb-3 overflow-hidden">
                        <div className="w-1/2 h-full bg-white" />
                      </div>
                      <div className="text-[13px] text-white/80 text-center">System</div>
                    </button>

                    {/* Light Theme */}
                    <button
                      onClick={() => setTheme('light')}
                      className={cn(
                        "flex-1 p-4 rounded-lg border-2 transition-all",
                        theme === 'light'
                          ? "border-blue-500 bg-blue-500/10"
                          : "border-white/10 hover:border-white/20"
                      )}
                    >
                      <div className="w-full aspect-[4/3] rounded-md bg-white mb-3 border border-white/20" />
                      <div className="text-[13px] text-white/80 text-center">Light</div>
                    </button>

                    {/* Dark Theme */}
                    <button
                      onClick={() => setTheme('dark')}
                      className={cn(
                        "flex-1 p-4 rounded-lg border-2 transition-all",
                        theme === 'dark'
                          ? "border-blue-500 bg-blue-500/10"
                          : "border-white/10 hover:border-white/20"
                      )}
                    >
                      <div className="w-full aspect-[4/3] rounded-md bg-[#1a1a1a] mb-3 border border-white/20" />
                      <div className="text-[13px] text-white/80 text-center">Dark</div>
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'domains' && (
            <>
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-[20px] font-semibold text-white">Domains</h2>
              </div>

              {/* Coming Soon Message */}
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <h3 className="text-[18px] font-medium text-white/80 mb-2">Coming Soon</h3>
                  <p className="text-[14px] text-white/40">Domain management features will be available soon.</p>
                </div>
              </div>
            </>
          )}

          {activeTab === 'integrations' && (
            <>
              <h2 className="text-[20px] font-semibold text-white mb-8">Integrations</h2>

              {/* Coming Soon Message */}
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <h3 className="text-[18px] font-medium text-white/80 mb-2">Coming Soon</h3>
                  <p className="text-[14px] text-white/40">Third-party integration features will be available soon.</p>
                </div>
              </div>
            </>
          )}

          {activeTab === 'profile' && (
            <>
              <h2 className="text-[20px] font-semibold text-white mb-8">Profile</h2>

              {/* Avatar */}
              <div className="mb-8">
                <h3 className="text-[15px] font-medium text-white mb-4">Avatar</h3>
                <div className="flex items-center justify-end">
                  <Avatar className="h-16 w-16">
                    <AvatarFallback className="bg-blue-600 text-white text-2xl font-bold">
                      A
                    </AvatarFallback>
                  </Avatar>
                </div>
              </div>

              {/* Username */}
              <div className="mb-6 pb-6 border-b border-white/10">
                <h3 className="text-[15px] font-medium text-white mb-4">Username</h3>
                <div className="flex items-center justify-between p-4 rounded-lg bg-[#2a2a2a]/50 border border-white/5">
                  <span className="text-[14px] text-white">Annam Madhukar reddy</span>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Edit size={14} className="text-white/60" />
                  </Button>
                </div>
              </div>

              {/* Email */}
              <div className="mb-8 pb-8 border-b border-white/10">
                <h3 className="text-[15px] font-medium text-white mb-4">Email</h3>
                <div className="p-4 rounded-lg bg-[#2a2a2a]/50 border border-white/5">
                  <span className="text-[14px] text-white">annammadhukarreddy53@gmail.com</span>
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
              <h2 className="text-[20px] font-semibold text-white mb-4">Plans and Billing</h2>
              <p className="text-[13px] text-white/60">View and manage your subscription</p>
            </div>
          )}

          {activeTab === 'help' && (
            <div>
              <h2 className="text-[20px] font-semibold text-white mb-4">Help Center</h2>
              <p className="text-[13px] text-white/60">Get help and support</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
