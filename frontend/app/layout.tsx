import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Cyber Incident Tracker",
  description: "Vendor risk monitoring and incident tracking"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
