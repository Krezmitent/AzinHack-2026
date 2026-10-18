import type { Metadata } from "next";
import Dashboard from "./Dashboard";

export const metadata: Metadata = {
  title: "Your Grant Board",
  description: "Manage your startup profile, review matched grant opportunities, and prepare application drafts in AutoGrant.",
  robots: { index: false, follow: false }
};

export default function DashboardPage() {
  return <Dashboard />;
}
