import { C, arrow, bg, footer, node, title } from "./common.mjs";

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx);
  title(slide, ctx, "Данные и cache", "polyglot persistence под разные типы нагрузки");
  node(slide, ctx, 80, 190, 210, 98, "PostgreSQL", "projects, tasks, status\ntransactional core", "#eff6ff", "#93c5fd");
  node(slide, ctx, 80, 350, 210, 98, "MongoDB", "reports, audit-like docs\nflexible report shape", "#ecfdf5", "#86efac");
  node(slide, ctx, 80, 510, 210, 82, "S3 / MinIO", "cold storage design\nraw agent outputs", "#f8fafc", "#cbd5e1");
  node(slide, ctx, 970, 210, 210, 110, "Valkey", "Redis-like TTL counters\nrate limit + hot state", "#fff7ed", "#fdba74");
  node(slide, ctx, 470, 260, 260, 130, "Services", "Project Intake\nRisk Analysis\nReport Service\nAPI Gateway", C.white, C.blue);
  arrow(slide, ctx, 470, 300, 290, 240, C.blue);
  arrow(slide, ctx, 470, 350, 290, 400, C.green);
  arrow(slide, ctx, 730, 318, 970, 265, C.amber);
  ctx.addShape(slide, { x: 370, y: 468, w: 470, h: 70, fill: "#eef2ff", line: ctx.line("#c7d2fe", 1) });
  ctx.addText(slide, { x: 396, y: 488, w: 430, h: 26, text: "Причина выбора: не все данные одинаковые. Статусы требуют транзакций, отчеты гибкой схемы, лимиты TTL counters.", fontSize: 17, bold: true, color: C.ink });
  footer(slide, ctx, 7);
  return slide;
}
