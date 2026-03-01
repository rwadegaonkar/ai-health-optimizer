"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "H" },
  { href: "/food-log", label: "Food Log", icon: "F" },
  { href: "/wearables", label: "Wearables", icon: "W" },
  { href: "/insights", label: "Insights", icon: "I" },
  { href: "/settings", label: "Settings", icon: "S" },
];

interface SidebarProps {
  userName: string;
  onLogout: () => void;
}

export function Sidebar({ userName, onLogout }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-lg font-bold text-gray-900">Health Optimizer</h1>
        <p className="text-sm text-gray-500 mt-1">{userName}</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              pathname === item.href
                ? "bg-primary-50 text-primary-700"
                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            )}
          >
            <span className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-xs font-bold">
              {item.icon}
            </span>
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <button
          onClick={onLogout}
          className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
