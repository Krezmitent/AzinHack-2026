import type { Metadata } from "next";
import "@fontsource/dm-sans/400.css";
import "@fontsource/dm-sans/500.css";
import "@fontsource/dm-sans/600.css";
import "@fontsource/dm-sans/700.css";
import "@fontsource/dm-sans/800.css";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "AutoGrant | A clearer route to your next grant", template: "%s | AutoGrant" },
  description: "Find startup grants, review their sources and fit, and prepare applications with AutoGrant.",
  openGraph: {
    type: "website",
    siteName: "AutoGrant",
    title: "AutoGrant | A clearer route to your next grant",
    description: "The source, the fit, and the next step in one place.",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "AutoGrant — A clearer route to your next grant" }]
  },
  twitter: { card: "summary_large_image", images: ["/opengraph-image"] }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
