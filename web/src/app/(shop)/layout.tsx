import type { ReactNode } from "react";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";

export default function ShopLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <Header />
      <main id="main" className="min-h-[60vh]">{children}</main>
      <Footer />
    </>
  );
}
