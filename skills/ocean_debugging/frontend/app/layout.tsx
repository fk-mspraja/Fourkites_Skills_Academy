import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FourKites Auto-RCA | Intelligent Root Cause Analysis",
  description: "AI-powered root cause analysis for shipment tracking issues",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-fourkites-navy/20">
          {children}
        </div>
      </body>
    </html>
  );
}
