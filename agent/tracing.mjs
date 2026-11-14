// Optional Arize AX tracing (OpenInference spans over OTLP), following Arize's Anthropic TypeScript integration.
//
// On only when ARIZE_SPACE_ID and ARIZE_API_KEY are set (capstone/.env, the shell, or the host's secrets); otherwise every
// helper below runs the function untouched and the kit behaves exactly as before. Tracing never changes a result.
//
//   ARIZE_SPACE_ID           base64 space id (ax spaces list)            required
//   ARIZE_API_KEY            Arize API key                               required, never committed
//   ARIZE_PROJECT_NAME       project the traces land in                  default orbita-crm-agent
//   ARIZE_COLLECTOR_ENDPOINT OTLP/HTTP traces endpoint                   default https://otlp.arize.com/v1/traces (US)
//   ORBITA_TRACE_HIDE_IO=1   keep transcripts and CRM values out of the spans (production with real customer data)
//
// One trace per agent run:  orbita.update (CHAIN)  ->  pre-checks (GUARDRAIL)  ->  Anthropic Messages (LLM, auto)
//                                                  ->  validator (GUARDRAIL: raw answer in, corrections out)
// Explore answers get their own trace: orbita.explore (CHAIN) -> Anthropic Messages (LLM).

import crypto from "node:crypto";

const ON = Boolean(process.env.ARIZE_SPACE_ID && process.env.ARIZE_API_KEY);
const HIDE = process.env.ORBITA_TRACE_HIDE_IO === "1";
export const PROJECT = process.env.ARIZE_PROJECT_NAME || "orbita-crm-agent";
let provider = null; let tracer = null; let otel = null; let instrumentation = null; let SC = null;

/** Starts the tracer provider once. Must run before the Anthropic client is created. */
export async function initTracing() {
  if (!ON || provider) return Boolean(provider);
  // the SDK's own OpenTelemetry spans would duplicate the OpenInference ones (@anthropic-ai/sdk >= 0.134)
  if (process.env.ANTHROPIC_OPEN_TELEMETRY == null) process.env.ANTHROPIC_OPEN_TELEMETRY = "false";
  otel = await import("@opentelemetry/api");
  const { AsyncLocalStorageContextManager } = await import("@opentelemetry/context-async-hooks");
  const { TracerProvider, BatchSpanProcessor } = await import("@opentelemetry/sdk-trace");
  const { OTLPTraceExporter } = await import("@opentelemetry/exporter-trace-otlp-proto");
  const { resourceFromAttributes } = await import("@opentelemetry/resources");
  const { ATTR_SERVICE_NAME } = await import("@opentelemetry/semantic-conventions");
  SC = await import("@arizeai/openinference-semantic-conventions");
  const { AnthropicInstrumentation } = await import("@arizeai/openinference-instrumentation-anthropic");
  const { registerInstrumentations } = await import("@opentelemetry/instrumentation");

  provider = new TracerProvider({
    resource: resourceFromAttributes({ [ATTR_SERVICE_NAME]: PROJECT, [SC.SEMRESATTRS_PROJECT_NAME]: PROJECT }),
    // OpenTelemetry 3.x: processors take an options object ({ exporter }), not the exporter itself
    spanProcessors: [new BatchSpanProcessor({ exporter: new OTLPTraceExporter({
      url: process.env.ARIZE_COLLECTOR_ENDPOINT || "https://otlp.arize.com/v1/traces",
      headers: { "arize-space-id": process.env.ARIZE_SPACE_ID, "arize-api-key": process.env.ARIZE_API_KEY },
    }) })],
  });
  otel.context.setGlobalContextManager(new AsyncLocalStorageContextManager().enable());
  otel.trace.setGlobalTracerProvider(provider);
  instrumentation = new AnthropicInstrumentation({ traceConfig: HIDE ? { hideInputs: true, hideOutputs: true } : {} });
  registerInstrumentations({ instrumentations: [instrumentation], tracerProvider: provider });
  tracer = otel.trace.getTracer("orbita-crm-agent");
  return true;
}

/** ESM: the Anthropic class is patched by hand, right after it is imported and before a client exists. */
export function instrumentAnthropic(Anthropic) {
  if (instrumentation) instrumentation.manuallyInstrument(Anthropic);
}

/** Sends the pending spans; a CLI calls it before exiting, the server on shutdown. */
export async function flushTracing() {
  if (provider) await provider.forceFlush();
}
export async function shutdownTracing() {
  if (provider) await provider.shutdown();
}

const json = (v) => (typeof v === "string" ? v : JSON.stringify(v));
/** Short, stable id of the prompt the agent ran with: the dashboard can then compare prompt versions. */
export const promptVersion = (system) => crypto.createHash("sha256").update(system).digest("hex").slice(0, 10);

/**
 * Runs fn inside a span. kind: CHAIN, GUARDRAIL, TOOL, AGENT... (OpenInference). input/output are recorded unless
 * ORBITA_TRACE_HIDE_IO=1. fn receives a handle: setInput(value), setOutput(value), set(attrs), ids() -> { traceId, spanId }.
 */
export async function inSpan(name, { kind = "CHAIN", input, attrs = {}, metadata, sessionId, userId, tags } = {}, fn) {
  const noop = { setInput() {}, setOutput() {}, set() {}, ids: () => ({ traceId: null, spanId: null }) };
  if (!tracer) return fn(noop);
  return tracer.startActiveSpan(name, async (span) => {
    const set = (a) => { for (const [k, v] of Object.entries(a)) if (v != null) span.setAttribute(k, typeof v === "object" ? json(v) : v); };
    set({ [SC.SemanticConventions.OPENINFERENCE_SPAN_KIND]: kind, ...attrs });
    if (input !== undefined && !HIDE) set({ [SC.INPUT_VALUE]: json(input), [SC.INPUT_MIME_TYPE]: typeof input === "string" ? "text/plain" : "application/json" });
    if (metadata) set({ [SC.METADATA]: json(metadata) });
    if (sessionId) set({ [SC.SESSION_ID]: sessionId });
    if (userId) set({ [SC.USER_ID]: userId });
    if (tags && tags.length) span.setAttribute(SC.TAG_TAGS, tags);
    const h = {
      setInput(v) { if (v !== undefined && !HIDE) set({ [SC.INPUT_VALUE]: json(v), [SC.INPUT_MIME_TYPE]: typeof v === "string" ? "text/plain" : "application/json" }); },
      setOutput(v) { if (v !== undefined && !HIDE) set({ [SC.OUTPUT_VALUE]: json(v), [SC.OUTPUT_MIME_TYPE]: typeof v === "string" ? "text/plain" : "application/json" }); },
      set,
      ids: () => ({ traceId: span.spanContext().traceId, spanId: span.spanContext().spanId }),
    };
    try {
      const r = await fn(h);
      span.setStatus({ code: otel.SpanStatusCode.OK });
      return r;
    } catch (e) {
      span.recordException(e);
      span.setStatus({ code: otel.SpanStatusCode.ERROR, message: e.message });
      throw e;
    } finally {
      span.end();
    }
  });
}
export const tracingOn = () => Boolean(tracer);
