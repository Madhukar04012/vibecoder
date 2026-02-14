import React from 'react';
import { Play, Upload, Sparkles, Settings, ChevronDown, User, Moon, Sun, GitBranch } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useGitStore } from '@/stores/gitStore';
import { useUIStore } from '@/stores/uiStore';

export const TopNavigationBar: React.FC = () => {
    const currentProject = useWorkspaceStore((state) => state.currentProject);
    const currentBranch = useGitStore((state) => state.currentBranch);
    const branches = useGitStore((state) => state.branches);
    const switchBranch = useGitStore((state) => state.switchBranch);
    const toggleAIPanel = useUIStore((state) => state.toggleAIPanel);
    const theme = useUIStore((state) => state.theme);
    const setTheme = useUIStore((state) => state.setTheme);

    return (
        <div className="h-[35px] bg-[#252526] border-b border-[#3E3E42] flex items-center justify-between px-4 flex-shrink-0">
            {/* Left Section */}
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded flex items-center justify-center">
                        <span className="text-white text-xs font-bold">CI</span>
                    </div>
                    <span className="text-[#CCCCCC] text-sm font-semibold">{currentProject}</span>
                </div>

                <div className="h-4 w-px bg-[#3E3E42]" />

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-[#CCCCCC] hover:bg-[#2A2D2E] text-xs gap-1.5 px-2"
                        >
                            <GitBranch className="w-3.5 h-3.5" />
                            {currentBranch}
                            <ChevronDown className="w-3 h-3" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="bg-[#252526] border-[#3E3E42]">
                        {branches.map((branch) => (
                            <DropdownMenuItem
                                key={branch.name}
                                onClick={() => switchBranch(branch.name)}
                                className="text-[#CCCCCC] hover:bg-[#2A2D2E] cursor-pointer"
                            >
                                {branch.name}
                                {branch.current && <span className="ml-2 text-[#007ACC]">✓</span>}
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator className="bg-[#3E3E42]" />
                        <DropdownMenuItem className="text-[#CCCCCC] hover:bg-[#2A2D2E] cursor-pointer">
                            Create new branch...
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>

            {/* Center Section */}
            <div className="flex items-center gap-2">
                <Button
                    size="sm"
                    className="h-7 bg-[#007ACC] hover:bg-[#0098FF] text-white text-xs gap-1.5 px-3"
                >
                    <Play className="w-3.5 h-3.5" />
                    Run
                </Button>
                <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-[#CCCCCC] hover:bg-[#2A2D2E] text-xs gap-1.5 px-3"
                >
                    <Upload className="w-3.5 h-3.5" />
                    Deploy
                </Button>
                <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-[#CCCCCC] hover:bg-[#2A2D2E] text-xs gap-1.5 px-3"
                    onClick={toggleAIPanel}
                >
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Assistant
                </Button>
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-2">
                <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 w-7 p-0 text-[#CCCCCC] hover:bg-[#2A2D2E]"
                    onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                    title="Toggle Theme"
                >
                    {theme === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                </Button>
                <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 w-7 p-0 text-[#CCCCCC] hover:bg-[#2A2D2E]"
                    title="Settings"
                >
                    <Settings className="w-4 h-4" />
                </Button>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 w-7 p-0 text-[#CCCCCC] hover:bg-[#2A2D2E] rounded-full"
                            title="User Menu"
                        >
                            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                                <User className="w-3.5 h-3.5 text-white" />
                            </div>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-[#252526] border-[#3E3E42]">
                        <DropdownMenuItem className="text-[#CCCCCC] hover:bg-[#2A2D2E] cursor-pointer">
                            Profile
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-[#CCCCCC] hover:bg-[#2A2D2E] cursor-pointer">
                            Settings
                        </DropdownMenuItem>
                        <DropdownMenuSeparator className="bg-[#3E3E42]" />
                        <DropdownMenuItem className="text-[#CCCCCC] hover:bg-[#2A2D2E] cursor-pointer">
                            Sign out
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </div>
    );
};