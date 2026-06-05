import { C, arrow, bg, footer, title } from "./common.mjs";

const steps = [
  ["POST", "API Gateway", "rate limit in Valkey"],
  ["202", "Project Intake", "task_id + ProjectSubmitted"],
  ["Kafka", "Event Bus", "retention, replay, groups"],
  ["Run", "Risk Analysis", "multi-agent workflow"],
  ["Save", "Report Service", "risk matrix + markdown"],
  ["Audit", "Audit / Notify", "events and NotificationSent"],
];

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, "#f8fafc");
  title(slide, ctx, "EDA: почему Kafka", "слабая связность и replay событий");
  const y = 300;
  steps.forEach((s, i) => {
    const x = 72 + i * 190;
    ctx.addShape(slide, { x, y, w: 154, h: 112, fill: C.white, line: ctx.line(i === 2 ? C.amber : C.line, i === 2 ? 2 : 1) });
    ctx.addText(slide, { x: x + 16, y: y + 14, w: 120, h: 20, text: s[0], fontSize: 15, bold: true, color: i === 2 ? C.amber : C.blue });
    ctx.addText(slide, { x: x + 16, y: y + 40, w: 122, h: 22, text: s[1], fontSize: 16, bold: true, color: C.ink });
    ctx.addText(slide, { x: x + 16, y: y + 70, w: 122, h: 32, text: s[2], fontSize: 11.5, color: C.muted });
    if (i < steps.length - 1) arrow(slide, ctx, x + 154, y + 56, x + 185, y + 56, i === 1 || i === 2 ? C.amber : C.blue);
  });
  ctx.addShape(slide, { x: 94, y: 158, w: 1016, h: 74, fill: "#fff7ed", line: ctx.line("#fed7aa", 1) });
  ctx.addText(slide, { x: 120, y: 180, w: 960, h: 28, text: "RabbitMQ/NATS проще для маленького MVP; Kafka выбрана для production-like EDA: retention, consumer groups, replay, partitions и Grafana lag metrics.", fontSize: 20, bold: true, color: "#9a3412" });
  ctx.addText(slide, { x: 108, y: 500, w: 980, h: 42, text: "Live proof: published_to_kafka=true, event_bus=kafka_redpanda, Risk Analysis формирует отчет асинхронно после ProjectSubmitted.", fontSize: 18, color: C.ink });
  footer(slide, ctx, 5);
  return slide;
}
