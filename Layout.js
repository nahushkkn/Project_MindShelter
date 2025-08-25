import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { createPageUrl } from "@/utils";
import { Brain, Calendar, User, Settings, Home, Volume2, VolumeX } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";

const navigationItems = [
  {
    title: "Explore Realms",
    url: createPageUrl("Home"),
    icon: Home,
  },
  {
    title: "My Sessions",
    url: createPageUrl("Sessions"),
    icon: Calendar,
  },
  {
    title: "Profile",
    url: createPageUrl("Profile"),
    icon: User,
  },
];

export default function Layout({ children, currentPageName }) {
  const location = useLocation();
  const [ambientEnabled, setAmbientEnabled] = useState(true);
  const [audioContext, setAudioContext] = useState(null); // This state is declared but not used in the provided snippet.

  // Don't play ambient sounds in live sessions
  const isLiveSession = currentPageName === "LiveSession" || location.pathname.includes("LiveSession");

  useEffect(() => {
    if (!isLiveSession && ambientEnabled) {
      // Create audio elements for ambient sounds
      const waterAudio = new Audio();
      const musicAudio = new Audio();
      
      // Using royalty-free nature sounds URLs (you would replace these with actual hosted files)
      waterAudio.src = "https://www.soundjay.com/misc/sounds/water-stream-01.mp3";
      musicAudio.src = "https://www.soundjay.com/misc/sounds/ambient-music-01.mp3";
      
      waterAudio.loop = true;
      musicAudio.loop = true;
      waterAudio.volume = 0.3;
      musicAudio.volume = 0.2;
      
      const playAmbient = async () => {
        try {
          await waterAudio.play();
          await musicAudio.play();
        } catch (error) {
          console.log("Audio autoplay prevented - user interaction required");
        }
      };
      
      playAmbient();
      
      return () => {
        waterAudio.pause();
        musicAudio.pause();
      };
    }
  }, [ambientEnabled, isLiveSession]);

  return (
    <div className="min-h-screen relative overflow-hidden">
      <style>{`
        :root {
          --glass-bg: rgba(212, 116, 30, 0.85);
          --glass-border: rgba(255, 255, 255, 0.15);
          --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
          --gradient-primary: linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%);
          --gradient-secondary: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
          --text-primary: #1f2937;
          --text-secondary: #374151;
          --text-muted: #6b7280;
          --text-light: #f9fafb;
          --text-amber-dark: #fef3c7;
          --text-amber-light: #fed7aa;
        }
        
        .glass-morphism {
          background: var(--glass-bg);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid var(--glass-border);
          box-shadow: var(--glass-shadow);
        }
        
        .sidebar-glass {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        .gradient-bg {
          background: var(--gradient-primary);
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: -1;
        }
        
        .floating-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(60px);
          animation: float 8s ease-in-out infinite;
          opacity: 0.3;
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-30px) rotate(180deg); }
        }
        
        .ambient-glow {
          position: absolute;
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
          border-radius: 50%;
          filter: blur(80px);
          animation: pulse 6s ease-in-out infinite;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 0.2; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(1.2); }
        }

        .text-dark { color: var(--text-primary); }
        .text-dark-secondary { color: var(--text-secondary); }
        .text-dark-muted { color: var(--text-muted); }
        .text-amber-dark { color: var(--text-amber-dark); }
        .text-amber-light { color: var(--text-amber-light); }
      `}</style>
      
      {/* Enhanced ambient background */}
      <div className="gradient-bg">
        <div className="floating-orb" style={{
          top: '15%',
          left: '10%',
          width: '300px',
          height: '300px',
          background: 'linear-gradient(45deg, #3b82f6, #1d4ed8)',
          animationDelay: '0s'
        }} />
        <div className="floating-orb" style={{
          top: '50%',
          right: '10%',
          width: '250px',
          height: '250px',
          background: 'linear-gradient(45deg, #6366f1, #4f46e5)',
          animationDelay: '3s'
        }} />
        <div className="floating-orb" style={{
          bottom: '25%',
          left: '20%',
          width: '200px',
          height: '200px',
          background: 'linear-gradient(45deg, #8b5cf6, #7c3aed)',
          animationDelay: '6s'
        }} />
        <div className="ambient-glow" style={{top: '20%', right: '25%'}} />
        <div className="ambient-glow" style={{bottom: '30%', left: '15%', animationDelay: '3s'}} />
      </div>

      <SidebarProvider>
        <div className="flex w-full relative z-10">
          <Sidebar className="sidebar-glass border-r border-gray-200">
            <SidebarHeader className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                    <Brain className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="font-bold text-gray-900 text-lg">Mind Shelter</h2>
                    <p className="text-xs text-gray-600">Reflective Storytelling</p>
                  </div>
                </div>
                {!isLiveSession && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setAmbientEnabled(!ambientEnabled)}
                    className="text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  >
                    {ambientEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                  </Button>
                )}
              </div>
            </SidebarHeader>
            
            <SidebarContent className="p-4">
              <SidebarGroup>
                <SidebarGroupLabel className="text-xs font-medium text-gray-600 uppercase tracking-wider px-2 py-2">
                  Navigation
                </SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {navigationItems.map((item) => (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton 
                          asChild 
                          className={`text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition-all duration-300 rounded-xl mb-2 ${
                            location.pathname === item.url ? 'bg-blue-50 text-blue-700 shadow-sm' : ''
                          }`}
                        >
                          <Link to={item.url} className="flex items-center gap-3 px-4 py-3">
                            <item.icon className="w-5 h-5" />
                            <span className="font-medium">{item.title}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            </SidebarContent>

            <SidebarFooter className="border-t border-gray-200 p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                  <span className="text-white font-medium text-sm">U</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 text-sm truncate">Welcome</p>
                  <p className="text-xs text-gray-600 truncate">You're not alone</p>
                </div>
              </div>
            </SidebarFooter>
          </Sidebar>

          <main className="flex-1 flex flex-col">
            <header className="glass-morphism border-b border-white/10 px-6 py-4 md:hidden">
              <div className="flex items-center gap-4">
                <SidebarTrigger className="text-amber-dark hover:bg-white/10 p-2 rounded-lg transition-colors duration-200" />
                <h1 className="text-xl font-semibold text-amber-dark">Mind Shelter</h1>
              </div>
            </header>

            <div className="flex-1 overflow-auto">
              {children}
            </div>
          </main>
        </div>
      </SidebarProvider>
    </div>
  );
}
