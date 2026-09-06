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
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-12">{children}</div>
      </body>
    </html>
  );
}
