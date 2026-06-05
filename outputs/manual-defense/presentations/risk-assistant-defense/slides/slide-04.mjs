import { C, arrow, bg, footer, node, title } from "./common.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx);
  title(slide, ctx, "C4 L2: контейнеры и связи", "микросервисная декомпозиция");
  node(slide, ctx, 72, 305, 150, 82, "User", "HTTP/JSON", "#eff6ff", "#93c5fd");
  node(slide, ctx, 270, 292, 178, 112, "HAProxy", "Ingress Controller\nentry point + balancing", "#fefce8", "#facc15");
  node(slide, ctx, 492, 292, 170, 106, "API Gateway", "routing + rate limit", "#eef2ff", "#818cf8");
  node(slide, ctx, 718, 128, 168, 92, "Project Intake", "task + ProjectSubmitted", C.white, C.line);
  node(slide, ctx, 718, 292, 168, 92, "Report Service", "GET reports", C.white, C.line);
  node(slide, ctx, 718, 456, 168, 92, "Audit Service", "event trail", C.white, C.line);
  node(slide, ctx, 950, 128, 170, 92, "Risk Analysis", "multi-agent workflow", "#ecfdf5", "#86efac");
  node(slide, ctx, 950, 456, 170, 92, "Notification", "ReportGenerated", "#ecfeff", "#67e8f9");
  node(slide, ctx, 940, 292, 198, 92, "Kafka / Redpanda", "domain events", "#fff7ed", "#fdba74");
  arrow(slide, ctx, 222, 346, 270, 346, C.blue);
  arrow(slide, ctx, 448, 346, 492, 346, C.blue);
  arrow(slide, ctx, 662, 330, 718, 174, C.blue);
  arrow(slide, ctx, 662, 346, 718, 338, C.blue);
  arrow(slide, ctx, 662, 362, 718, 502, C.blue);
  arrow(slide, ctx, 886, 174, 940, 322, C.amber);
  arrow(slide, ctx, 1038, 292, 1038, 220, C.amber);
  arrow(slide, ctx, 1038, 384, 1038, 456, C.amber);
  ctx.addText(slide, { x: 74, y: 575, w: 1040, h: 36, text: "Сервисы масштабируются независимо; downstream consumers можно добавлять без изменения Project Intake.", fontSize: 18, bold: true, color: C.ink });
  footer(slide, ctx, 4);
  return slide;
}
