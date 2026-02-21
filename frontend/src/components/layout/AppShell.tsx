import { useState, type PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";

import { cn } from "../../lib/utils/cn";
import { Button } from "../ui/Button";

const navItems = [
  { to: "/", label: "Overview" },
  { to: "/sync", label: "Sync" },
  { to: "/ask", label: "Ask" },
  { to: "/metrics", label: "Metrics" },
  { to: "/ops", label: "Ops" },
  { to: "/design-system", label: "Design System" }
];

export function AppShell({ children }: PropsWithChildren) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="app-grid">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <aside
        className={cn(
          "border-r border-[var(--border)] bg-[var(--surface-1)] p-4 md:relative md:block",
          menuOpen ? "block" : "hidden md:block"
        )}
      >
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--ink-2)]">
            Redmine RAG
          </p>
          <h1 className="section-title mt-1 text-2xl font-semibold text-[var(--ink-1)]">Console</h1>
        </div>
        <nav aria-label="Main navigation" className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                cn(
                  "block rounded-xl px-3 py-2 text-sm font-medium",
                  isActive
                    ? "bg-[var(--brand-soft)] text-[var(--brand-strong)]"
                    : "text-[var(--ink-1)] hover:bg-[var(--surface-2)]"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[color:rgba(245,247,239,0.92)] px-4 py-3 backdrop-blur">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.12em] text-[var(--ink-2)]">Operator workspace</p>
              <p className="text-sm text-[var(--ink-1)]">Sync, ask, metrics and health in one place.</p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              className="md:hidden"
              onClick={() => setMenuOpen((prev) => !prev)}
              aria-expanded={menuOpen}
              aria-controls="main-navigation"
            >
              Menu
            </Button>
          </div>
        </header>

        <main id="main-content" className="mx-auto w-full max-w-6xl space-y-6 px-4 py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
