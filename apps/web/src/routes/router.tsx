import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { ChatPage } from "./ChatPage";
import { ConversationsPage } from "./ConversationsPage";
import { PlaceholderPage } from "./PlaceholderPage";
import { TeamPage } from "./TeamPage";
import { WorkspacePage } from "./WorkspacePage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <ChatPage /> },
      { path: "chat", element: <ChatPage /> },
      { path: "conversations", element: <ConversationsPage /> },
      {
        path: "projects",
        element: (
          <PlaceholderPage
            phase="Phase 4 (proposed)"
            epic="E20 — Projects"
            description="A lightweight grouping layer over conversations, shown in the design mockup but not yet in the approved plan — logged as a Phase 4 candidate epic pending confirmation. See progress.md."
          />
        ),
      },
      {
        path: "workflows",
        element: (
          <PlaceholderPage
            phase="Phase 4"
            epic="E18 — Workflow Automation"
            description="Event-triggered AI actions routed to Slack, Sheets, or email land here."
          />
        ),
      },
      {
        path: "usage",
        element: (
          <PlaceholderPage
            phase="Phase 2"
            epic="E6 / E10 — Cost Attribution & Billing"
            description="Token volume, spend, active users, and latency dashboards land here."
          />
        ),
      },
      {
        path: "audit",
        element: (
          <PlaceholderPage
            phase="Phase 2"
            epic="E6 — Audit Logs & Cost Attribution"
            description="An exportable, immutable record of who used what, when, and at what cost."
          />
        ),
      },
      { path: "team", element: <TeamPage /> },
      {
        path: "integrations",
        element: (
          <PlaceholderPage
            phase="Phase 2"
            epic="E7 / E8 / E9 — Slack, WhatsApp, Google Sheets"
            description="Connect Afridock to Slack, WhatsApp Business, and Google Sheets."
          />
        ),
      },
      {
        path: "billing",
        element: (
          <PlaceholderPage
            phase="Phase 2"
            epic="E10 — Usage-Based Billing"
            description="Plans, seats, and usage-based billing via Paystack/Flutterwave land here."
          />
        ),
      },
      {
        path: "resilience",
        element: (
          <PlaceholderPage
            phase="Phase 3"
            epic="E11 / E12 — Offline Queue & Local Model Caching"
            description="Connectivity status, queued-request counts, and local model caching controls land here."
          />
        ),
      },
      { path: "workspace", element: <WorkspacePage /> },
    ],
  },
]);
