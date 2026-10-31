import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Toaster } from "@/components/ui/toaster";
import { LanguageProvider } from "@/context/LanguageContext";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "JanSahayak AI — Multilingual Indian Government Scheme Explainer",
  description:
    "Empowering citizens across India with transparent, AI-driven explanations and personalized eligibility checks for Indian central and state government schemes in English, Hindi, and Telugu.",
  keywords: [
    "JanSahayak AI",
    "Indian Government Schemes",
    "Sarkari Yojana",
    "PM-KISAN",
    "PMAY",
    "Scholarships",
    "Multilingual AI",
    "Hindi",
    "Telugu",
    "Civic Tech",
  ],
  authors: [{ name: "JanSahayak AI Team" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans antialiased">
        <LanguageProvider>
          <Header />
          <main className="flex-1 flex flex-col">{children}</main>
          <Footer />
          <Toaster />
        </LanguageProvider>
      </body>
    </html>
  );
}
