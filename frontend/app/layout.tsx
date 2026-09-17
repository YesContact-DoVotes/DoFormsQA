import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "AI QA Agent — Autonomous Testing Platform",
  description: "Autonomous E2E & Exploratory Testing for Web Applications",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-blue-500/30 selection:text-blue-200">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
