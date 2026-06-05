import { C, bg, footer, title } from "./common.mjs";

const rows = [
  ["ТЗ, User Stories, Use Cases, NFR", "docs/high-level-scope.md"],
  ["C4 L1-L3 + Sequence Diagram", "docs/c4-and-sequence.md"],
  ["3+ microservices, Kafka/EDA", "services/, contracts/, infra/kafka/"],
  ["RDBMS + NoSQL + Valkey cache", "infra/postgres, Helm values"],
  ["Kubernetes, Cilium, autoscaling", "infra/kubernetes/cluster/"],
  ["Terraform + ArgoCD + Ansible", "infra/terraform, infra/argocd, infra/ansible"],
  ["Istio, HAProxy, Keepalived, rate limit", "infra/kubernetes/gateway, mesh"],
  ["Observability, CI/CD, Locust validation", "infra/observability, infra/ci, tests/load"],
];

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, C.white);
  title(slide, ctx, "Требования преподавателя закрыты", "критерии и доказательства");
  const x1 = 86, x2 = 650, y0 = 160, rh = 52;
  ctx.addShape(slide, { x: x1, y: 130, w: 1080, h: 34, fill: C.dark });
  ctx.addText(slide, { x: x1 + 18, y: 139, w: 380, h: 16, text: "Требование", fontSize: 13, bold: true, color: C.white });
  ctx.addText(slide, { x: x2 + 18, y: 139, w: 350, h: 16, text: "Где проверять", fontSize: 13, bold: true, color: C.white });
  rows.forEach((row, i) => {
    const y = y0 + i * rh;
    ctx.addShape(slide, { x: x1, y, w: 1080, h: rh - 4, fill: i % 2 ? "#f8fafc" : "#eef2ff", line: ctx.line("#e2e8f0", 0.6) });
    ctx.addText(slide, { x: x1 + 18, y: y + 15, w: 500, h: 18, text: row[0], fontSize: 15, bold: true, color: C.ink });
    ctx.addText(slide, { x: x2 + 18, y: y + 15, w: 470, h: 18, text: row[1], fontSize: 13, color: C.muted });
    ctx.addText(slide, { x: 1128, y: y + 14, w: 36, h: 18, text: "OK", fontSize: 13, bold: true, color: C.green, align: "right" });
  });
  footer(slide, ctx, 3);
  return slide;
}
