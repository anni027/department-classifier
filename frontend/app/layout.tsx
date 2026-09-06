import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Taqneeq Department Finder",
  description: "Find the Taqneeq department that matches your interests, skills and working style.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Halftone grain sits above the gradient, below the content. */}
        <div className="tq-grain" aria-hidden="true" />
        <div className="tq-page" style={{ paddingBottom: 72 }}>
          {children}
        </div>
      </body>
    </html>
  );
}
