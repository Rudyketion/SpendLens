import type { Metadata } from "next";
import { ReactNode } from "react";

import { MobileNav, Nav } from "@/components/nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "SpendLens — Personal finance, clarified",
  description:
    "Upload a bank statement and instantly see where your money goes, with AI-categorized transactions.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex">
          <Nav />
          <div className="flex-1 min-w-0 flex flex-col">
            <MobileNav />
            <main className="flex-1 px-4 sm:px-8 py-6 max-w-[1400px] w-full mx-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
