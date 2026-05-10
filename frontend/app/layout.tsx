import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AIVIS",
  description: "AI Video Intelligence System",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
