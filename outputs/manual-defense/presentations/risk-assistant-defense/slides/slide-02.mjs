import { C, arrow, bg, footer, node, title } from "./common.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx);
  title(slide, ctx, "Что делает система", "идея и пользовательский сценарий");
  node(slide, ctx, 78, 190, 250, 120, "Пользователь", "Отправляет описание проекта и получает task_id", "#eff6ff", "#93c5fd");
  node(slide, ctx, 386, 150, 260, 160, "Risk Assistant", "Запускает многоагентный анализ: требования, риски, mitigation plan, валидация", C.white, C.blue);
  node(slide, ctx, 714, 190, 250, 120, "Отчет", "Markdown-матрица рисков, рекомендации и audit trail", "#ecfdf5", "#86efac");
  node(slide, ctx, 998, 190, 180, 120, "Администратор", "Grafana, ArgoCD, kubectl, alerts", "#fffbeb", "#fcd34d");
  arrow(slide, ctx, 328, 250, 386, 230, C.blue);
  arrow(slide, ctx, 646, 230, 714, 250, C.green);
  arrow(slide, ctx, 964, 250, 998, 250, C.amber);
  ctx.addText(slide, {
    x: 126,
    y: 400,
    w: 980,
    h: 74,
    text: "Главная архитектурная идея: прием запроса и тяжелая обработка разделены событием ProjectSubmitted в Kafka. Пользователь быстро получает task_id, а downstream сервисы обрабатывают событие независимо.",
    fontSize: 22,
    color: C.ink,
  });
  ctx.addText(slide, { x: 126, y: 510, w: 980, h: 40, text: "Проверенный live-сценарий: POST /projects/analyze -> Kafka event -> Risk Analysis -> GET /reports/{task_id}.", fontSize: 18, bold: true, color: C.blue });
  footer(slide, ctx, 2);
  return slide;
}
