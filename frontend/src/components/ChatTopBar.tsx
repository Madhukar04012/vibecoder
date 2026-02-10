import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Bell, Home, Settings } from "lucide-react";
import { SettingsPanel } from "@/components/SettingsPanel";

export function ChatTopBar() {
  return (
    <nav className="shrink-0 border-b border-white/5 bg-[#0d0d0d] p-3 backdrop-blur-sm">
      <div className="flex items-center justify-between">
        <Button size="icon" className="rounded-full h-9 w-9" variant="ghost">
          <Home className="h-5 w-5 text-white/60" />
          <span className="sr-only">Home</span>
        </Button>
        
        <Button
          size="icon"
          className="rounded-full h-9 w-9 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400"
        >
          <Bell className="h-5 w-5" />
          <span className="sr-only">Notifications</span>
        </Button>
        
        <Dialog>
          <DialogTrigger asChild>
            <Button size="icon" className="rounded-full h-9 w-9" variant="ghost">
              <Settings className="h-5 w-5 text-white/60" />
              <span className="sr-only">Settings</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="w-[90vw] h-[90vh] max-w-[1500px] p-0 bg-[#1a1a1a] border-white/10">
            <SettingsPanel />
          </DialogContent>
        </Dialog>
      </div>
    </nav>
  );
}
