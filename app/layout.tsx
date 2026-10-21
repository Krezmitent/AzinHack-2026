import type { Metadata } from "next";
import "@fontsource/syne/700.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/600.css";
import "@fontsource/manrope/700.css";
import "@fontsource/manrope/800.css";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "AutoGrant | Find grants. Know why.", template: "%s | AutoGrant" },
  description: "Find startup grants, review their sources and fit, and prepare applications with AutoGrant.",
  openGraph: {
    type: "website",
    siteName: "AutoGrant",
    title: "AutoGrant | Find grants. Know why.",
    description: "The source, the fit, and the next step in one place.",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "AutoGrant — Find grants. Know why." }]
  },
  twitter: { card: "summary_large_image", images: ["/opengraph-image"] }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
