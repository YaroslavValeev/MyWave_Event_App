"use client";

import { AppHeader } from "@/components/AppHeader";
import { WelcomeJourney } from "@/components/WelcomeJourney";

/**
 * Champ App start: goal-first onboarding, no changes to API or permissions.
 * Every privileged action still resolves through existing backend-controlled pages.
 */
export default function HomePage() {
  return (
    <>
      <AppHeader />
      <main id="main">
        <WelcomeJourney />
      </main>
    </>
  );
}
