import { C, bg, footer } from "./common.mjs";

const commands = [
  "python3 scripts/check_submission.py",
  ".venv/bin/python -m pytest -q",
  "scripts/defense_smoke.sh",
  "START_PORT_FORWARD=1 scripts/demo_e2e.sh",
  "locust -f tests/load/locustfile.py --host http://localhost:8080 --headless",
];

export async function slide10(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, C.dark);
  ctx.addText(slide, { x: 64, y: 42, w: 520, h: 24, text: "готовый порядок демонстрации", fontSize: 15, bold: true, color: "#38bdf8" });
  ctx.addText(slide, { x: 64, y: 78, w: 780, h: 58, text: "Как защищать за 5-7 минут", fontSize: 34, bold: true, color: C.white, face: ctx.fonts.title });
  ctx.addShape(slide, { x: 64, y: 138, w: 1120, h: 420, fill: "#111827", line: ctx.line("#334155", 1) });
  const items = [
    ["1", "Открыть criteria-matrix и high-level scope", "Показать прямое покрытие требований."],
    ["2", "Показать C4 и sequence", "Объяснить Gateway -> Kafka -> Risk Analysis -> Report."],
    ["3", "Запустить smoke", "Nodes Ready, ArgoCD Healthy, 6 services on ci-final-demo."],
    ["4", "Запустить E2E", "project_title, published_to_kafka=true, report approved."],
    ["5", "Закрыть observability/CI/CD", "Prometheus targets, Locust, local pipeline."],
  ];
  items.forEach((item, i) => {
    const y = 166 + i * 72;
    ctx.addText(slide, { x: 96, y, w: 42, h: 34, text: item[0], fontSize: 28, bold: true, color: "#38bdf8", align: "center" });
    ctx.addText(slide, { x: 160, y: y + 2, w: 430, h: 22, text: item[1], fontSize: 19, bold: true, color: C.white });
    ctx.addText(slide, { x: 160, y: y + 30, w: 430, h: 24, text: item[2], fontSize: 14, color: "#cbd5e1" });
  });
  commands.forEach((cmd, i) => {
    const y = 160 + i * 66;
    ctx.addShape(slide, { x: 650, y, w: 482, h: 42, fill: "#020617", line: ctx.line("#1e293b", 1) });
    ctx.addText(slide, { x: 668, y: y + 13, w: 450, h: 16, text: cmd, fontSize: 12.5, color: "#dbeafe", face: ctx.fonts.mono });
  });
  ctx.addText(slide, { x: 80, y: 604, w: 1040, h: 24, text: "Финальная фраза: проект демонстрирует не только код, но и платформенный контур эксплуатации.", fontSize: 19, bold: true, color: "#facc15" });
  footer(slide, ctx, 10);
  return slide;
}
