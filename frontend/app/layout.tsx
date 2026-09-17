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
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased selection:bg-blue-500/20 selection:text-blue-700">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
