'use client'
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "./component/navbar";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (
    <html lang="en">
      <body className={inter.className}>
        <div>
          <div className="nav">
            <Navbar />
          </div>
          <div className="layout">
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
