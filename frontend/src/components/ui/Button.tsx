import type { ButtonHTMLAttributes } from "react";

import { cn } from "../../lib/utils/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";

type Size = "sm" | "md";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantClass: Record<Variant, string> = {
  primary:
    "bg-[var(--brand)] text-white border border-transparent hover:bg-[var(--brand-strong)] active:translate-y-[1px]",
  secondary:
    "bg-[var(--surface-0)] text-[var(--ink-1)] border border-[var(--border)] hover:bg-[var(--surface-2)]",
  ghost: "bg-transparent text-[var(--ink-1)] border border-transparent hover:bg-[var(--surface-2)]",
  danger:
    "bg-[#a6322f] text-white border border-transparent hover:bg-[#8f2522] active:translate-y-[1px]"
};

const sizeClass: Record<Size, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-10 px-4 text-sm"
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  type = "button",
  ...props
}: Props) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
        variantClass[variant],
        sizeClass[size],
        className
      )}
      {...props}
    />
  );
}
