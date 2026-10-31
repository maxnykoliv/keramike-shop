import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond, Manrope } from "next/font/google";
import type { ReactNode } from "react";

import { serverEnv } from "@/env";
import { site } from "@/shared/config/site";
import { ConsentBanner } from "@/shared/ui";

import "@/shared/styles/globals.css";

import { Providers } from "./providers";

const serif = Cormorant_Garamond({ subsets: ["latin", "cyrillic"], weight: ["500", "600"], variable: "--font-serif", display: "swap" });
const sans = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-sans", display: "swap" });

export function generateMetadata(): Metadata {
  return {
    metadataBase: new URL(serverEnv().SITE_URL),
    title: { default: site.title, template: `%s — ${site.name}` },
    description: site.description,
    openGraph: { siteName: site.name, locale: "uk_UA", type: "website" },
  };
}

// eslint-disable-next-line no-restricted-syntax -- колір рядка браузера = --color-bg
export const viewport: Viewport = { themeColor: "#f7f5f0", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="uk" className={`${serif.variable} ${sans.variable}`}>
      <body>
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:bg-bg focus:p-3">
          Перейти до змісту
        </a>
        <Providers>
          {children}
          <ConsentBanner />
        </Providers>
      </body>
    </html>
  );
}
