/**
 * Scenarios 01–09 via HTTP API (Playwright request).
 * Requires running API: E2E_API_BASE (default http://127.0.0.1:8000)
 * Scenario 10 (Xiaomi) remains manual.
 */
import { expect, test, type APIRequestContext } from "@playwright/test";

const API = process.env.E2E_API_BASE || "http://127.0.0.1:8010";

async function devLogin(request: APIRequestContext, email: string, role: string) {
  const res = await request.post(`${API}/api/v1/auth/dev-login`, {
    data: { email, role },
  });
  if (res.status() === 404 || res.status() === 403) {
    test.skip(true, "dev-login unavailable (non-development API)");
  }
  expect(res.ok(), await res.text()).toBeTruthy();
  const body = await res.json();
  return {
    token: body.access_token as string,
    headers: { Authorization: `Bearer ${body.access_token}` },
  };
}

async function seedEvent(request: APIRequestContext, slug: string) {
  const org = await devLogin(request, `${slug}-org@example.com`, "organizer");
  const created = await request.post(`${API}/api/v1/events`, {
    headers: org.headers,
    data: { slug, title: `E2E ${slug}`, status: "draft" },
  });
  expect(created.status(), await created.text()).toBe(201);
  const eventId = (await created.json()).id as number;
  await request.patch(`${API}/api/v1/events/${eventId}/status`, {
    headers: org.headers,
    data: { status: "registration_open" },
  });
  return { eventId, org };
}

test.describe("Champ App API scenarios", () => {
  test.beforeAll(async ({ request }) => {
    let reachable = false;
    try {
      const health = await request.get(`${API}/health`);
      reachable = health.ok();
      if (!reachable) {
        const alt = await request.get(`${API}/api/v1/health`);
        reachable = alt.ok();
      }
    } catch {
      reachable = false;
    }
    test.skip(!reachable, `API not reachable at ${API} (start uvicorn on this port)`);
  });

  test("SC01 organizer prepares event and publishes result", async ({ request }) => {
    const { eventId, org } = await seedEvent(request, `sc01-${Date.now()}`);
    await request.put(`${API}/api/v1/events/${eventId}/rules-profile`, {
      headers: org.headers,
      data: {
        governing_body: "FVLS",
        sanction_body: "IWWF",
        discipline_codes: ["wakeskim"],
        scoring_mode: "manual",
      },
    });
    const athlete = await devLogin(request, `sc01-ath-${Date.now()}@example.com`, "participant");
    const app = await request.post(`${API}/api/v1/events/${eventId}/applications`, {
      headers: athlete.headers,
      data: { category_id: null },
    });
    expect(app.status()).toBe(201);
    const pid = (await app.json()).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/applications/${pid}`, {
      headers: org.headers,
      data: { status: "accepted" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/status`, {
      headers: org.headers,
      data: { status: "live" },
    });
    const result = await request.post(`${API}/api/v1/events/${eventId}/results`, {
      headers: org.headers,
      data: { participant_id: pid, score: 95, place: 1 },
    });
    expect(result.status()).toBe(201);
    const rid = (await result.json()).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "verified" },
    });
    const pub = await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "published" },
    });
    expect(pub.ok()).toBeTruthy();
    const board = await request.get(`${API}/api/v1/events/${eventId}/scoreboard`);
    expect((await board.json()).total).toBeGreaterThanOrEqual(1);
  });

  test("SC02 participant guidance after apply", async ({ request }) => {
    const { eventId } = await seedEvent(request, `sc02-${Date.now()}`);
    const athlete = await devLogin(request, `sc02-ath-${Date.now()}@example.com`, "participant");
    await request.post(`${API}/api/v1/events/${eventId}/applications`, {
      headers: athlete.headers,
      data: { category_id: null },
    });
    const guidance = await request.get(`${API}/api/v1/events/${eventId}/guidance`, {
      headers: athlete.headers,
    });
    expect(guidance.ok()).toBeTruthy();
    const body = await guidance.json();
    expect(body.role).toBe("participant");
    expect(body.journey_phase).toBeTruthy();
  });

  test("SC03 judge submits score sheet", async ({ request }) => {
    const { eventId, org } = await seedEvent(request, `sc03-${Date.now()}`);
    await request.put(`${API}/api/v1/events/${eventId}/rules-profile`, {
      headers: org.headers,
      data: {
        governing_body: "FVLS",
        sanction_body: "IWWF",
        discipline_codes: ["wakesurf_boat"],
        scoring_mode: "structured",
      },
    });
    const athlete = await devLogin(request, `sc03-ath-${Date.now()}@example.com`, "participant");
    const app = await request.post(`${API}/api/v1/events/${eventId}/applications`, {
      headers: athlete.headers,
      data: { category_id: null },
    });
    const pid = (await app.json()).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/applications/${pid}`, {
      headers: org.headers,
      data: { status: "accepted" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/status`, {
      headers: org.headers,
      data: { status: "live" },
    });
    const judge = await devLogin(request, `sc03-judge-${Date.now()}@example.com`, "judge");
    const engine = await request.get(`${API}/api/v1/events/${eventId}/scoring/engine`, {
      headers: judge.headers,
    });
    expect(engine.ok()).toBeTruthy();
    const meta = await engine.json();
    expect(meta.engine).not.toBe("MANUAL_PLACE");
    const criteria: Record<string, number> = {};
    const keys: string[] = Array.isArray(meta.criteria)
      ? meta.criteria
      : meta.criteria_keys || ["overall"];
    for (const key of keys) {
      criteria[key] = 80;
    }
    const score = await request.post(`${API}/api/v1/events/${eventId}/judge-scores`, {
      headers: judge.headers,
      data: {
        participant_id: pid,
        attempt_no: 1,
        engine: meta.engine,
        criteria,
      },
    });
    expect(score.status(), await score.text()).toBe(201);
  });

  test("SC04 chief/organizer approves protocol revision", async ({ request }) => {
    const { eventId, org } = await seedEvent(request, `sc04-${Date.now()}`);
    await request.put(`${API}/api/v1/events/${eventId}/rules-profile`, {
      headers: org.headers,
      data: {
        governing_body: "FVLS",
        sanction_body: "IWWF",
        discipline_codes: ["wakeskim"],
        scoring_mode: "manual",
      },
    });
    const athlete = await devLogin(request, `sc04-ath-${Date.now()}@example.com`, "participant");
    const pid = (
      await (
        await request.post(`${API}/api/v1/events/${eventId}/applications`, {
          headers: athlete.headers,
          data: { category_id: null },
        })
      ).json()
    ).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/applications/${pid}`, {
      headers: org.headers,
      data: { status: "accepted" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/status`, {
      headers: org.headers,
      data: { status: "live" },
    });
    const rid = (
      await (
        await request.post(`${API}/api/v1/events/${eventId}/results`, {
          headers: org.headers,
          data: { participant_id: pid, score: 88, place: 1 },
        })
      ).json()
    ).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "verified" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "published" },
    });
    const rev = await request.post(`${API}/api/v1/events/${eventId}/official-protocol/revisions`, {
      headers: org.headers,
      data: { note: "SC04" },
    });
    expect(rev.status(), await rev.text()).toBe(201);
    const revId = (await rev.json()).id as number;
    const pdf = await request.get(
      `${API}/api/v1/events/${eventId}/official-protocol/revisions/${revId}/pdf`,
      { headers: org.headers },
    );
    expect(pdf.ok()).toBeTruthy();
    const buf = Buffer.from(await pdf.body());
    expect(buf.subarray(0, 4).toString("utf8")).toBe("%PDF");
  });

  test("SC05 guest scoreboard sees only published", async ({ request }) => {
    const { eventId, org } = await seedEvent(request, `sc05-${Date.now()}`);
    const athlete = await devLogin(request, `sc05-ath-${Date.now()}@example.com`, "participant");
    const pid = (
      await (
        await request.post(`${API}/api/v1/events/${eventId}/applications`, {
          headers: athlete.headers,
          data: { category_id: null },
        })
      ).json()
    ).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/applications/${pid}`, {
      headers: org.headers,
      data: { status: "accepted" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/status`, {
      headers: org.headers,
      data: { status: "live" },
    });
    const rid = (
      await (
        await request.post(`${API}/api/v1/events/${eventId}/results`, {
          headers: org.headers,
          data: { participant_id: pid, score: 70, place: 1 },
        })
      ).json()
    ).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "verified" },
    });
    const guestDraft = await request.get(`${API}/api/v1/events/${eventId}/scoreboard`);
    expect((await guestDraft.json()).total).toBe(0);
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "published" },
    });
    const guestPub = await request.get(`${API}/api/v1/events/${eventId}/scoreboard`);
    expect((await guestPub.json()).total).toBe(1);
  });

  test("SC06 offline publication draft idempotency key", async ({ request }) => {
    const { eventId, org } = await seedEvent(request, `sc06-${Date.now()}`);
    await request.patch(`${API}/api/v1/events/${eventId}/status`, {
      headers: org.headers,
      data: { status: "live" },
    });
    const payload = {
      type: "news",
      title: "Offline queue",
      body: "once",
      author_role: "organizer",
      intent: "publish",
      idempotency_key: `sc06-${Date.now()}`,
    };
    const a = await request.post(`${API}/api/v1/events/${eventId}/publications`, {
      headers: org.headers,
      data: payload,
    });
    const b = await request.post(`${API}/api/v1/events/${eventId}/publications`, {
      headers: org.headers,
      data: payload,
    });
    expect(a.status()).toBe(201);
    expect(b.status()).toBe(201);
    expect((await a.json()).id).toBe((await b.json()).id);
  });

  test("SC07 conflict: void published before silent overwrite", async ({ request }) => {
    const { eventId, org } = await seedEvent(request, `sc07-${Date.now()}`);
    const athlete = await devLogin(request, `sc07-ath-${Date.now()}@example.com`, "participant");
    const pid = (
      await (
        await request.post(`${API}/api/v1/events/${eventId}/applications`, {
          headers: athlete.headers,
          data: { category_id: null },
        })
      ).json()
    ).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/applications/${pid}`, {
      headers: org.headers,
      data: { status: "accepted" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/status`, {
      headers: org.headers,
      data: { status: "live" },
    });
    const rid = (
      await (
        await request.post(`${API}/api/v1/events/${eventId}/results`, {
          headers: org.headers,
          data: { participant_id: pid, score: 60, place: 1 },
        })
      ).json()
    ).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "verified" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "published" },
    });
    // published cannot jump back to draft without void
    const illegal = await request.patch(
      `${API}/api/v1/events/${eventId}/results/${rid}/status`,
      { headers: org.headers, data: { status: "draft" } },
    );
    expect(illegal.ok()).toBeFalsy();
    const voided = await request.patch(
      `${API}/api/v1/events/${eventId}/results/${rid}/status`,
      { headers: org.headers, data: { status: "void" } },
    );
    expect(voided.ok()).toBeTruthy();
    const history = await request.get(
      `${API}/api/v1/events/${eventId}/results/${rid}/history`,
      { headers: org.headers },
    );
    expect(history.ok()).toBeTruthy();
  });

  test("SC08 protocol revision creates new version", async ({ request }) => {
    const { eventId, org } = await seedEvent(request, `sc08-${Date.now()}`);
    await request.put(`${API}/api/v1/events/${eventId}/rules-profile`, {
      headers: org.headers,
      data: {
        governing_body: "FVLS",
        sanction_body: "IWWF",
        discipline_codes: ["wakeskim"],
        scoring_mode: "manual",
      },
    });
    const athlete = await devLogin(request, `sc08-ath-${Date.now()}@example.com`, "participant");
    const pid = (
      await (
        await request.post(`${API}/api/v1/events/${eventId}/applications`, {
          headers: athlete.headers,
          data: { category_id: null },
        })
      ).json()
    ).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/applications/${pid}`, {
      headers: org.headers,
      data: { status: "accepted" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/status`, {
      headers: org.headers,
      data: { status: "live" },
    });
    const rid = (
      await (
        await request.post(`${API}/api/v1/events/${eventId}/results`, {
          headers: org.headers,
          data: { participant_id: pid, score: 77, place: 1 },
        })
      ).json()
    ).id as number;
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "verified" },
    });
    await request.patch(`${API}/api/v1/events/${eventId}/results/${rid}/status`, {
      headers: org.headers,
      data: { status: "published" },
    });
    const r1 = await request.post(`${API}/api/v1/events/${eventId}/official-protocol/revisions`, {
      headers: org.headers,
      data: { note: "v1" },
    });
    const r2 = await request.post(`${API}/api/v1/events/${eventId}/official-protocol/revisions`, {
      headers: org.headers,
      data: { note: "v2 correction" },
    });
    expect((await r1.json()).revision_no).toBe(1);
    expect((await r2.json()).revision_no).toBe(2);
  });

  test("SC09 role security: participant cannot create news", async ({ request }) => {
    const { eventId, org } = await seedEvent(request, `sc09-${Date.now()}`);
    await request.patch(`${API}/api/v1/events/${eventId}/status`, {
      headers: org.headers,
      data: { status: "live" },
    });
    const athlete = await devLogin(request, `sc09-ath-${Date.now()}@example.com`, "participant");
    const denied = await request.post(`${API}/api/v1/events/${eventId}/publications`, {
      headers: athlete.headers,
      data: {
        type: "news",
        title: "Hack",
        body: "no",
        author_role: "participant",
        intent: "publish",
      },
    });
    expect(denied.status()).toBe(403);
    const mismatch = await request.post(`${API}/api/v1/events/${eventId}/publications`, {
      headers: athlete.headers,
      data: {
        type: "post",
        title: "Hack role",
        body: "no",
        author_role: "organizer",
        intent: "draft",
      },
    });
    expect(mismatch.status()).toBe(403);
  });

  test("SC10 android device acceptance is manual", async () => {
    test.info().annotations.push({
      type: "manual",
      description: "See docs/OPERATIONS/XIAOMI14_TEST_CHECKLIST.md — APK BLOCKED without JDK/SDK",
    });
    test.skip(true, "Xiaomi 14 device acceptance requires physical phone + APK/PWA");
  });
});
