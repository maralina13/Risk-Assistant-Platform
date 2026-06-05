import { C, bg, footer, metric, title } from "./common.mjs";

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, C.white);
  title(slide, ctx, "Observability и отказоустойчивость", "что проверено live");
  ctx.addShape(slide, { x: 74, y: 156, w: 500, h: 390, fill: "#f8fafc", line: ctx.line("#cbd5e1", 1) });
  ctx.addText(slide, { x: 104, y: 184, w: 340, h: 24, text: "Telemetry stack", fontSize: 20, bold: true, color: C.ink });
  metric(slide, ctx, 108, 248, "10/10", "Prometheus pod targets healthy", C.green);
  metric(slide, ctx, 326, 248, "1", "Grafana dashboard ConfigMap", C.blue);
  metric(slide, ctx, 108, 388, "1", "PrometheusRule alert pack", C.amber);
  ctx.addText(slide, { x: 326, y: 392, w: 190, h: 64, text: "Loki, Tempo and OpenTelemetry manifests are included for logs/traces.", fontSize: 15, color: C.muted });
  ctx.addShape(slide, { x: 650, y: 156, w: 500, h: 390, fill: "#0f172a", line: ctx.line("#334155", 1) });
  ctx.addText(slide, { x: 680, y: 184, w: 340, h: 24, text: "Resilience validation", fontSize: 20, bold: true, color: C.white });
  ctx.addText(slide, { x: 690, y: 248, w: 150, h: 38, text: "859", fontSize: 36, bold: true, color: "#38bdf8" });
  ctx.addText(slide, { x: 690, y: 292, w: 180, h: 36, text: "Locust requests, 0 failures", fontSize: 15, color: "#cbd5e1" });
  ctx.addText(slide, { x: 900, y: 248, w: 150, h: 38, text: "429", fontSize: 36, bold: true, color: "#facc15" });
  ctx.addText(slide, { x: 900, y: 292, w: 180, h: 36, text: "rate limiter observed under harder run", fontSize: 15, color: "#cbd5e1" });
  ctx.addText(slide, { x: 690, y: 388, w: 390, h: 60, text: "Circuit breaker demo: report-service scaled to 0, temporary failures appeared, rollout restored to 2/2.", fontSize: 18, bold: true, color: C.white });
  footer(slide, ctx, 8);
  return slide;
}
