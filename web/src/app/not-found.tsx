import type { Metadata } from "next";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { NotFoundContent } from "@/components/NotFoundContent";

export const metadata: Metadata = { title: "Сторінку не знайдено", robots: { index: false } };

export default function NotFound() {
  return (
    <>
      <Header />
      <main id="main"><NotFoundContent /></main>
      <Footer />
    </>
  );
}
