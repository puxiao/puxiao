import type { Metadata } from "next";
import Image from "next/image";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import styles from "./page.module.css";
import tongji from "./tongji.js";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Puxiao.com",
  description: "I am a front-end developer. Nice to meet you.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
        <head>
          <script>{tongji}</script>
        </head>
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
        <footer className={styles.footer}>
        <a href="https://github.com/puxiao" target="_blank" rel="noopener noreferrer" >
          <span className={styles.logo}>
            <Image src="/github.svg" alt="Github" width={18} height={18} />
          </span>
          https://github.com/puxiao
        </a>
      </footer>
      </body>
    </html>
  );
}
