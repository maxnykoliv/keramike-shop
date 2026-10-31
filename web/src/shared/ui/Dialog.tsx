"use client";

import * as RadixDialog from "@radix-ui/react-dialog";
import type { ReactNode } from "react";

import { Icon } from "./Icon";

export function Dialog({
  open, onOpenChange, title, description, children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-40 bg-text/30 data-[state=open]:animate-[fade-up_200ms_ease-out]" />
        <RadixDialog.Content
          className="fixed inset-x-0 bottom-0 z-50 max-h-[90dvh] overflow-y-auto rounded-t-[2px] bg-bg p-6 shadow-none md:inset-auto md:top-1/2 md:left-1/2 md:w-[520px] md:-translate-x-1/2 md:-translate-y-1/2 md:p-10">
          <div className="mb-6 flex items-start justify-between gap-4">
            <RadixDialog.Title className="t-h2">{title}</RadixDialog.Title>
            <RadixDialog.Close className="-m-2 p-2" aria-label="Закрити">
              <Icon name="close" />
            </RadixDialog.Close>
          </div>
          {description ? (
            <RadixDialog.Description className="mb-6 text-text-muted">{description}</RadixDialog.Description>
          ) : (
            <RadixDialog.Description className="sr-only">{title}</RadixDialog.Description>
          )}
          {children}
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}
