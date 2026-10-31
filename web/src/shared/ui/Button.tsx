import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/shared/lib/cn";

import { Spinner } from "./Spinner";

type Variant = "primary" | "secondary" | "ghost" | "link";
type Size = "lg" | "md" | "sm";

const base =
  "inline-flex items-center justify-center gap-2 rounded-[2px] t-label transition-colors duration-200 " +
  "disabled:cursor-not-allowed disabled:opacity-50 select-none";
const variants: Record<Variant, string> = {
  primary: "bg-button text-bg hover:bg-button-hover",
  secondary: "border border-button text-text hover:bg-button hover:text-bg",
  ghost: "text-text hover:bg-surface",
  link: "text-accent-strong underline underline-offset-4 decoration-1 hover:decoration-2 normal-case tracking-normal text-[15px] font-normal",
};
const sizes: Record<Size, string> = {
  lg: "min-h-14 px-8",
  md: "min-h-12 px-6 md:min-h-[52px]",
  sm: "min-h-11 px-4",
};

type CommonProps = {
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
  loading?: boolean;
  className?: string;
  children: ReactNode;
};

export function buttonClass({ variant = "primary", size = "md", fullWidth, className }: Omit<CommonProps, "children" | "loading">) {
  return cn(base, variants[variant], variant !== "link" && sizes[size], fullWidth && "w-full", className);
}

export function Button({
  variant, size, fullWidth, loading, className, children, disabled, type = "button", ...rest
}: CommonProps & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button type={type} className={buttonClass({ variant, size, fullWidth, className })}
      disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {loading ? <Spinner label="Зачекайте" /> : null}
      {children}
    </button>
  );
}

export function ButtonLink({
  href, variant, size, fullWidth, className, children, ...rest
}: CommonProps & { href: string; prefetch?: boolean; target?: string; rel?: string; onClick?: () => void; "data-testid"?: string }) {
  return (
    <Link href={href} className={buttonClass({ variant, size, fullWidth, className })} {...rest}>
      {children}
    </Link>
  );
}
