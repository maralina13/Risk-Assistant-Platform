import { C, bg, footer, node, title } from "./common.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, "#f1f5f9");
  title(slide, ctx, "Kubernetes platform layer", "локальная production-like инфраструктура");
  ctx.addShape(slide, { x: 68, y: 146, w: 1080, h: 400, fill: C.white, line: ctx.line("#94a3b8", 1.2) });
  ctx.addText(slide, { x: 92, y: 166, w: 240, h: 22, text: "cluster: risk-assistant", fontSize: 17, bold: true, color: C.ink });
  node(slide, ctx, 104, 220, 220, 90, "Node 1", "control-plane Ready\nCilium, workloads", "#eff6ff", "#93c5fd");
  node(slide, ctx, 104, 348, 220, 90, "Node 2", "worker Ready\nCilium, workloads", "#eff6ff", "#93c5fd");
  node(slide, ctx, 390, 214, 250, 98, "Platform infra", "Cilium CNI\nIstio service mesh\nHAProxy Ingress\nKeepalived manifests", "#f8fafc", "#cbd5e1");
  node(slide, ctx, 390, 350, 250, 98, "GitOps / IaC", "Terraform namespaces\nArgoCD App of Apps\nAnsible Strimzi role\nHelm chart", "#f8fafc", "#cbd5e1");
  node(slide, ctx, 706, 214, 180, 98, "Kafka", "risk-kafka-0\nRunning", "#fff7ed", "#fdba74");
  node(slide, ctx, 922, 214, 180, 98, "Data stores", "PostgreSQL\nMongoDB\nValkey", "#ecfdf5", "#86efac");
  node(slide, ctx, 706, 350, 396, 98, "Application namespace", "6 deployments, services, PDB, securityContext, ServiceMonitor", "#eef2ff", "#a5b4fc");
  ctx.addText(slide, { x: 86, y: 580, w: 1040, h: 34, text: "ArgoCD live: kafka, observability, platform-infra, risk-assistant, root app = Synced / Healthy.", fontSize: 18, bold: true, color: C.green });
  footer(slide, ctx, 6);
  return slide;
}
