import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { AuthGate } from "@/components/layout/auth-gate";
import { AppShell } from "@/components/layout/app-shell";

// Self-hosted so the GitHub Pages base path can never break the font URLs
const archivo = localFont({ src: "./fonts/archivo.woff2", weight: "400 700", variable: "--font-archivo", display: "swap" });
const bigShoulders = localFont({ src: "./fonts/big-shoulders.woff2", weight: "700 900", variable: "--font-big-shoulders", display: "swap" });

export const metadata: Metadata = {
  title: "Stay Jotivated Analytics",
  description: "Jovan Paige social media analytics",
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`h-full antialiased ${archivo.variable} ${bigShoulders.variable}`}>
      <body className="min-h-full bg-background text-foreground">
        <AuthGate>
          <AppShell>{children}</AppShell>
        </AuthGate>
      </body>
    </html>
  );
}
