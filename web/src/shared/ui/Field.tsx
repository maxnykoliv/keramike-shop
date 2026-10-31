import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

export type FieldIds = { inputId: string; describedBy: string | undefined; invalid: boolean };

/** Підпис над полем, підказка й помилка під ним, зв'язані через aria-describedby. */
export function Field({
  label, hint, error, className, children, id,
}: {
  label: ReactNode;
  hint?: ReactNode;
  error?: string | null;
  className?: string;
  id?: string;
  children: (ids: FieldIds) => ReactNode;
}) {
  const autoId = useId();
  const inputId = id ?? `f${autoId}`;
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={inputId} className="t-small font-medium">{label}</label>
      {children({ inputId, describedBy, invalid: Boolean(error) })}
      {hint ? <p id={hintId} className="t-small text-text-muted">{hint}</p> : null}
      {error ? <p id={errorId} role="alert" className="t-small text-error">{error}</p> : null}
    </div>
  );
}

const inputBase =
  "w-full min-h-12 bg-transparent border-0 border-b border-line-strong px-0 py-2 rounded-none " +
  "placeholder:text-text-muted/70 focus:outline-none focus:border-b-2 focus:border-text " +
  "aria-[invalid=true]:border-error transition-colors";

export function TextInput({ ids, className, ...props }: { ids: FieldIds } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input id={ids.inputId} aria-describedby={ids.describedBy} aria-invalid={ids.invalid || undefined}
      className={cn(inputBase, className)} {...props} />
  );
}

export function TextArea({ ids, className, ...props }: { ids: FieldIds } & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea id={ids.inputId} aria-describedby={ids.describedBy} aria-invalid={ids.invalid || undefined}
      className={cn(inputBase, "min-h-24 resize-y", className)} {...props} />
  );
}

export function Select({ ids, className, children, ...props }: { ids: FieldIds } & SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select id={ids.inputId} aria-describedby={ids.describedBy} aria-invalid={ids.invalid || undefined}
      className={cn(inputBase, "cursor-pointer appearance-none bg-[length:12px] pr-6", className)} {...props}>
      {children}
    </select>
  );
}
