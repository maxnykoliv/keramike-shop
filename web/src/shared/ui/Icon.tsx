import type { SVGProps } from "react";

/** Line icons with a 1.25 px stroke: one set for the whole site. */
const PATHS = {
  cart: "M3 4h2l2.2 10.2a1 1 0 0 0 1 .8h8.9a1 1 0 0 0 1-.8L20 8H6.3 M9 20a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z M17 20a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Z M20 20l-4-4",
  menu: "M4 7h16 M4 12h16 M4 17h16",
  close: "M6 6l12 12 M18 6L6 18",
  plus: "M12 5v14 M5 12h14",
  minus: "M5 12h14",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  check: "M5 12.5l4.5 4.5L19 7.5",
  telegram: "M21 4L3 11l6 2 2 6 3-4 5 4 2-15Z M9 13l9-7",
  calculator: "M6 3h12v18H6z M9 7h6 M9 11h1 M14 11h1 M9 15h1 M14 15h1 M9 18h1 M14 18h1",
  filter: "M4 6h16 M7 12h10 M10 18h4",
  trash: "M5 7h14 M10 11v6 M14 11v6 M7 7l1 13h8l1-13 M10 7V4h4v3",
  pin: "M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21Z M12 12a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z",
  door: "M6 21V4h12v17 M4 21h16 M14 12h1",
  share: "M8 12l8-5 M8 12l8 5 M6 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z M18 9a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z M18 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z",
  download: "M12 4v11 M7 10l5 5 5-5 M5 20h14",
  chevron: "M9 6l6 6-6 6",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 20, ...props }: { name: IconName; size?: number } & SVGProps<SVGSVGElement>) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.25}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" {...props}>
      <path d={PATHS[name]} />
    </svg>
  );
}
