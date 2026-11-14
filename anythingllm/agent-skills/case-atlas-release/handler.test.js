const test = require("node:test");
const assert = require("node:assert/strict");
const { runtime } = require("./handler");

const params = {
  stakeholder_id: "ana",
  file: "pedidos.csv",
  purpose: "investigar atrasos por semana",
  safeguards: "somente os campos necessários",
  columns: '["pedido_id","data_pedido","quantidade_pedida"]',
  date_from: "2026-09-01",
  date_to: "2026-10-31",
};

function makeContext({ workspace = "Case Atlas", chatId = 321, userId = 42, providerFails = false, unsupportedFilter = false, reuse = false } = {}) {
  const calls = [];
  const completions = [];
  const service = {
    request_id: "request-1",
    status: reuse ? "released" : "pending",
    origin_thread_id: "anythingllm:workspace:7:chat:321",
    ...(reuse ? { release_id: "a".repeat(32), scope: { file: "pedidos.csv", columns: ["pedido_id"], date_from: null, date_to: null }, row_count: 1 } : {}),
  };
  const release = {
    request_id: "request-1",
    release_id: "a".repeat(32),
    status: "released",
    scope: { file: "pedidos.csv", columns: ["pedido_id", "data_pedido"], date_from: null, date_to: null },
    artifact_sha256: "b".repeat(64),
    row_count: 8,
    decision: "partial",
  };
  const context = {
    policy: "POLICY_SECRET",
    stakeholder_policy: "ANA_POLICY_SECRET",
    stakeholder_profile: "ANA_PROFILE_SECRET",
  };
  const providerInstance = {
    async complete(messages) {
      completions.push(messages);
      if (providerFails) throw new Error("provider unavailable");
      const stakeholder = completions.length === 2;
      return {
        textResponse: JSON.stringify({
          outcome: "partial",
          reason: stakeholder ? "Aceito o recorte recente." : "Libero somente o período recente.",
          scope: unsupportedFilter ? { ...release.scope, filters: { cliente_id: "C-1" } } : release.scope,
        }),
      };
    },
  };
  const originalFetch = global.fetch;
  global.fetch = async (url, options) => {
    calls.push({ url: String(url), options, body: options?.body ? JSON.parse(options.body) : null });
    if (String(url).endsWith("/v1/decision-context")) return response(context);
    if (String(url).endsWith("/v1/requests")) return response(service, 201);
    if (String(url).includes("/v1/requests/") && String(url).endsWith("/decision")) {
      const body = JSON.parse(options.body);
      if (body.facilitator.outcome === "clarify" || body.stakeholder.outcome === "clarify") {
        return response({ request_id: "request-1", status: "clarify", release_id: null });
      }
      return response(release);
    }
    throw new Error(`unexpected URL ${url}`);
  };
  return {
    calls,
    completions,
    result: () => ({ runtimeArgs: { CASE_RELEASE_SERVICE_URL: "http://case-release:8091", CASE_RELEASE_API_TOKEN: "t".repeat(48), CASE_RELEASE_DOWNLOAD_BASE_URL: "https://llm.armelfelipe.com.br" }, super: { handlerProps: { invocation: { workspace_id: 7, user_id: userId, workspace: { name: workspace } } }, trackedChatId: chatId, chats: [{ from: "USER", content: "Precisamos entender atrasos e proteger clientes." }], providerInstance } }),
    restore: () => { global.fetch = originalFetch; },
  };
}

function response(value, status = 200) {
  return { ok: status >= 200 && status < 300, status, async json() { return value; } };
}

test("uses trusted AnythingLLM workspace, user and chat metadata, then returns stable download link", async () => {
  const fixture = makeContext();
  try {
    const result = await runtime.handler.call(fixture.result(), params);
    const created = fixture.calls.find((call) => call.url.endsWith("/v1/requests"));
    assert.equal(created.body.requester_id, "42");
    assert.equal(created.body.origin_thread_id, "anythingllm:workspace:7:chat:321");
    assert.equal(created.options.headers.Authorization, `Bearer ${"t".repeat(48)}`);
    assert.equal(fixture.completions.length, 2);
    const facilitatorRequest = JSON.parse(fixture.completions[0][1].content);
    assert.deepEqual(facilitatorRequest.requested_scope, {
      file: "pedidos.csv",
      columns: ["pedido_id", "data_pedido", "quantidade_pedida"],
      date_from: "2026-09-01",
      date_to: "2026-10-31",
    });
    const stakeholderRequest = JSON.parse(fixture.completions[1][1].content);
    assert.deepEqual(stakeholderRequest.requested_scope, facilitatorRequest.requested_scope);
    assert.match(fixture.completions[0][0].content, /POLICY_SECRET/);
    assert.match(result, /https:\/\/llm\.armelfelipe\.com\.br\/v1\/releases\/[a-f0-9]{32}\/download/, result);
    assert.doesNotMatch(result, /ANA_PROFILE_SECRET|POLICY_SECRET|t{48}/);
  } finally {
    fixture.restore();
  }
});

test("refuses invocation outside Case Atlas without contacting the service", async () => {
  const fixture = makeContext({ workspace: "Other workspace" });
  try {
    const result = await runtime.handler.call(fixture.result(), params);
    assert.match(result, /workspace Case Atlas/i);
    assert.equal(fixture.calls.length, 0);
  } finally {
    fixture.restore();
  }
});

test("fails closed when trusted chat metadata is absent", async () => {
  const fixture = makeContext({ chatId: null });
  try {
    const result = await runtime.handler.call(fixture.result(), params);
    assert.match(result, /não consegui identificar com segurança/i);
    assert.equal(fixture.calls.length, 0);
  } finally {
    fixture.restore();
  }
});

test("fails closed when authenticated user identity is absent", async () => {
  const fixture = makeContext({ userId: null });
  try {
    const result = await runtime.handler.call(fixture.result(), params);
    assert.match(result, /não consegui identificar com segurança/i);
    assert.equal(fixture.calls.length, 0);
  } finally {
    fixture.restore();
  }
});

test("provider failure is recorded as clarification and never publishes a link", async () => {
  const fixture = makeContext({ providerFails: true });
  try {
    const result = await runtime.handler.call(fixture.result(), params);
    const decisionCall = fixture.calls.find((call) => call.url.endsWith("/decision"));
    assert.equal(decisionCall.body.facilitator.outcome, "clarify");
    assert.equal(decisionCall.body.stakeholder.outcome, "clarify");
    assert.match(result, /clarify/);
    assert.doesNotMatch(result, /download/);
  } finally {
    fixture.restore();
  }
});

test("unsupported row filters become clarification instead of silently widening the release", async () => {
  const fixture = makeContext({ unsupportedFilter: true });
  try {
    const result = await runtime.handler.call(fixture.result(), params);
    const decisionCall = fixture.calls.find((call) => call.url.endsWith("/decision"));
    assert.equal(decisionCall.body.facilitator.outcome, "clarify");
    assert.equal(decisionCall.body.stakeholder.outcome, "clarify");
    assert.doesNotMatch(result, /download/);
  } finally {
    fixture.restore();
  }
});

test("reuses an existing release without loading facilitator context or invoking the model", async () => {
  const fixture = makeContext({ reuse: true });
  try {
    const result = await runtime.handler.call(fixture.result(), params);
    assert.equal(fixture.calls.length, 1);
    assert.equal(fixture.calls[0].url, "http://case-release:8091/v1/requests");
    assert.equal(fixture.completions.length, 0);
    assert.match(result, /"reused":true/);
    assert.match(result, /https:\/\/llm\.armelfelipe\.com\.br\/v1\/releases\/[a-f0-9]{32}\/download/);
  } finally {
    fixture.restore();
  }
});
