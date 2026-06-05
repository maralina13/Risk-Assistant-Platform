import { C, bg, footer, metric, pill } from "./common.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, C.dark);
  ctx.addText(slide, { x: 64, y: 52, w: 420, h: 24, text: "защита учебного проекта", fontSize: 15, bold: true, color: "#7dd3fc" });
  ctx.addText(slide, {
    x: 64,
    y: 110,
    w: 720,
    h: 124,
    text: "Multi-Agent Risk Assistant",
    fontSize: 46,
    bold: true,
    color: C.white,
    face: ctx.fonts.title,
  });
  ctx.addText(slide, {
    x: 68,
    y: 252,
    w: 650,
    h: 88,
    text: "Микросервисная event-driven платформа для анализа проектных рисков: Kafka, Kubernetes, GitOps, Service Mesh, Observability и CI/CD.",
    fontSize: 21,
    color: "#dbeafe",
  });
  pill(slide, ctx, 68, 370, 130, "Kafka / EDA", "#1e40af", C.white);
  pill(slide, ctx, 214, 370, 148, "Kubernetes", "#155e75", C.white);
  pill(slide, ctx, 378, 370, 122, "ArgoCD", "#166534", C.white);
  pill(slide, ctx, 516, 370, 142, "Observability", "#854d0e", C.white);
  ctx.addShape(slide, { x: 760, y: 92, w: 430, h: 430, fill: "#111827", line: ctx.line("#334155", 1) });
  metric(slide, ctx, 810, 140, "6", "микросервисов", "#38bdf8");
  metric(slide, ctx, 1010, 140, "2", "Kubernetes nodes Ready", "#4ade80");
  metric(slide, ctx, 810, 278, "10/10", "Prometheus targets healthy", "#4ade80");
  metric(slide, ctx, 1010, 278, "0", "Locust failures in normal run", "#facc15");
  ctx.addText(slide, { x: 810, y: 455, w: 320, h: 30, text: "Live image: localhost:5000/risk-assistant:ci-final-demo", fontSize: 14, color: "#cbd5e1" });
  footer(slide, ctx, 1);
  return slide;
}
