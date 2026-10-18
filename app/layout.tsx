import type { Metadata } from "next";
import "@fontsource/syne/700.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/600.css";
import "@fontsource/manrope/700.css";
import "@fontsource/manrope/800.css";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "AutoGrant | Find Grants That Fit", template: "%s | AutoGrant" },
  description: "Find startup grants that fit your business, review match reasons, and prepare application drafts with AutoGrant.",
  openGraph: {
    type: "website",
    siteName: "AutoGrant",
    title: "AutoGrant | Find Grants That Fit",
    description: "Discover grants. Understand the match. Make your case.",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "AutoGrant — Find funding that fits your startup" }]
  },
  twitter: { card: "summary_large_image", images: ["/opengraph-image"] }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
