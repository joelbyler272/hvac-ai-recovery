"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { Sidebar, MobileSidebar, MobileHeader } from "./sidebar";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("sidebar-collapsed") === "true";
    }
    return false;
  });

  useEffect(() => {
    if (!loading && !user) {
      router.push("/");
    }
  }, [user, loading, router]);

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-white">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ember" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-warm-white">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <MobileSidebar open={mobileOpen} onClose={() => setMobileOpen(false)} />
      <MobileHeader onMenuOpen={() => setMobileOpen(true)} />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
