"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Phone,
  Users,
  MessageSquare,
  Calendar,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/calls", label: "Calls", icon: Phone },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/conversations", label: "Conversations", icon: MessageSquare },
  { href: "/appointments", label: "Appointments", icon: Calendar },
  { href: "/reports", label: "Reports", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

function CallHookLogo({ collapsed }: { collapsed?: boolean }) {
  if (collapsed) {
    return (
      <svg viewBox="0 0 50 60" className="h-7 w-auto" aria-label="CallHook">
        <g transform="translate(4, 8)">
          <path
            d="M2 24 L16 44 L16 12 C16 5 21 0 28 0 C35 0 40 5 40 12"
            stroke="currentColor"
            strokeWidth="5"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M44 8 C48 4 48 -2 44 -4"
            stroke="#E86A2A"
            strokeWidth="2.5"
            fill="none"
            strokeLinecap="round"
            opacity="0.5"
          />
        </g>
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 360 80" className="h-8 w-auto" aria-label="CallHook">
      <g transform="translate(4, 8)">
        <path
          d="M2 24 L16 44 L16 12 C16 5 21 0 28 0 C35 0 40 5 40 12"
          stroke="currentColor"
          strokeWidth="5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M44 8 C48 4 48 -2 44 -4"
          stroke="#E86A2A"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
          opacity="0.5"
        />
        <path
          d="M48 12 C54 6 54 -4 48 -8"
          stroke="#E86A2A"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
          opacity="0.3"
        />
      </g>
      <text
        x="64"
        y="50"
        fontFamily="Inter, sans-serif"
        fontWeight="800"
        fontSize="40"
        letterSpacing="-1.5"
      >
        <tspan fill="currentColor">Call</tspan>
        <tspan fill="#E86A2A">Hook</tspan>
      </text>
    </svg>
  );
}

// Desktop sidebar
export function Sidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const pathname = usePathname();
  const { signOut } = useAuth();

  return (
    <aside
      className={`hidden md:flex flex-col min-h-screen bg-navy-deep text-white transition-all duration-200 ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      <div className={`flex items-center ${collapsed ? "justify-center p-3" : "justify-between p-6"}`}>
        <CallHookLogo collapsed={collapsed} />
        <button
          onClick={onToggle}
          className={`p-1 rounded hover:bg-navy-light transition-colors ${collapsed ? "hidden" : ""}`}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className="h-4 w-4 text-slate-muted" />
        </button>
      </div>

      {collapsed && (
        <button
          onClick={onToggle}
          className="mx-auto p-1 rounded hover:bg-navy-light transition-colors mb-2"
        >
          <ChevronRight className="h-4 w-4 text-slate-muted" />
        </button>
      )}

      <nav className={`flex-1 space-y-1 ${collapsed ? "px-1.5" : "px-3"}`}>
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={`flex items-center gap-3 rounded-lg text-sm font-medium transition-colors ${
                collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2.5"
              } ${
                isActive
                  ? "bg-ember/15 text-ember"
                  : "text-slate-muted hover:bg-navy-light hover:text-white"
              }`}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && item.label}
            </Link>
          );
        })}
      </nav>

      <div className={`border-t border-navy-light ${collapsed ? "p-1.5" : "p-3"}`}>
        <button
          onClick={() => signOut()}
          title={collapsed ? "Sign Out" : undefined}
          className={`flex items-center gap-3 rounded-lg text-sm font-medium text-slate-muted hover:bg-navy-light hover:text-white w-full transition-colors ${
            collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2.5"
          }`}
        >
          <LogOut className="h-5 w-5" />
          {!collapsed && "Sign Out"}
        </button>
      </div>
    </aside>
  );
}

// Mobile drawer
export function MobileSidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();
  const { signOut } = useAuth();

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <aside
        className={`fixed inset-y-0 left-0 w-64 bg-navy-deep text-white z-50 flex flex-col transform transition-transform duration-200 md:hidden ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between p-6">
          <CallHookLogo />
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-navy-light transition-colors"
          >
            <X className="h-5 w-5 text-slate-muted" />
          </button>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-ember/15 text-ember"
                    : "text-slate-muted hover:bg-navy-light hover:text-white"
                }`}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-navy-light">
          <button
            onClick={() => signOut()}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-muted hover:bg-navy-light hover:text-white w-full transition-colors"
          >
            <LogOut className="h-5 w-5" />
            Sign Out
          </button>
        </div>
      </aside>
    </>
  );
}

// Mobile header bar with menu toggle
export function MobileHeader({ onMenuOpen }: { onMenuOpen: () => void }) {
  return (
    <header className="md:hidden bg-navy-deep text-white px-4 py-3 flex items-center gap-3">
      <button onClick={onMenuOpen} className="p-1" aria-label="Open menu">
        <Menu className="h-5 w-5" />
      </button>
      <CallHookLogo />
    </header>
  );
}
