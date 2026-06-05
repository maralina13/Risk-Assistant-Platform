import { C, arrow, bg, footer, node, title } from "./common.mjs";

export async function slide09(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, "#f8fafc");
  title(slide, ctx, "CI/CD и GitOps", "проверенный delivery path");
  const y = 270;
  node(slide, ctx, 78, y, 160, 96, "Tests", "pytest\n10 passed", "#ecfdf5", "#86efac");
  node(slide, ctx, 282, y, 160, 96, "Build", "Docker/Kaniko target\nPython image", "#eff6ff", "#93c5fd");
  node(slide, ctx, 486, y, 180, 96, "Image", "localhost:5000\nci-final-demo", "#eef2ff", "#a5b4fc");
  node(slide, ctx, 710, y, 180, 96, "GitOps", "update Helm params\npush local Git", "#fff7ed", "#fdba74");
  node(slide, ctx, 934, y, 190, 96, "ArgoCD", "sync + rollout\nSynced / Healthy", "#ecfdf5", "#86efac");
  arrow(slide, ctx, 238, y + 48, 282, y + 48, C.blue);
  arrow(slide, ctx, 442, y + 48, 486, y + 48, C.blue);
  arrow(slide, ctx, 666, y + 48, 710, y + 48, C.amber);
  arrow(slide, ctx, 890, y + 48, 934, y + 48, C.green);
  ctx.addShape(slide, { x: 116, y: 466, w: 930, h: 58, fill: C.dark, line: ctx.line("#334155", 1) });
  ctx.addText(slide, { x: 142, y: 484, w: 880, h: 24, text: "IMAGE_TAG=ci-final-demo scripts/local_ci_pipeline.sh", fontSize: 22, bold: true, color: "#e0f2fe", face: ctx.fonts.mono });
  ctx.addText(slide, { x: 138, y: 560, w: 920, h: 34, text: "Целевой GitLab pipeline описан отдельно: Kaniko build, registry push, Helm update, ArgoCD sync.", fontSize: 17, color: C.ink });
  footer(slide, ctx, 9);
  return slide;
}
