import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { AuthGuard } from "../components/auth/AuthGuard";
import { AuditPage } from "./AuditPage";
import { ChatPage } from "./ChatPage";
import { ConversationsPage } from "./ConversationsPage";
import { LoginPage } from "./LoginPage";
import { PlaceholderPage } from "./PlaceholderPage";
import { SignupPage } from "./SignupPage";
import { TeamPage } from "./TeamPage";
import { UsagePage } from "./UsagePage";
import { WorkspacePage } from "./WorkspacePage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignupPage /> },
  {
    path: "/",
    element: (
      <AuthGuard>
        <AppShell />
      </AuthGuard>
    ),
    children: [
      { index: true, element: <ChatPage /> },
      { path: "chat", element: <ChatPage /> },
      { path: "chat/:conversationId", element: <ChatPage /> },
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
      { path: "usage", element: <UsagePage /> },
      { path: "audit", element: <AuditPage /> },
      { path: "team", element: <TeamPage /> },
      {
        path: "integrations",
        element: (
          <PlaceholderPage
            phase="Phase 2"
            epic="E7 / E8 / E9 — Slack, WhatsApp, Google Sheets"
            description="Connect Afrikdock to Slack, WhatsApp Business, and Google Sheets."
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
