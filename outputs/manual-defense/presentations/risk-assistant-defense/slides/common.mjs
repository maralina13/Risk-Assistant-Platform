export const C = {
  ink: "#111827",
  muted: "#5b6472",
  faint: "#eef2f7",
  line: "#cbd5e1",
  bg: "#f8fafc",
  blue: "#2563eb",
  cyan: "#0891b2",
  green: "#16a34a",
  amber: "#d97706",
  red: "#dc2626",
  dark: "#0f172a",
  white: "#ffffff",
};

export function bg(slide, ctx, color = C.bg) {
  ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill: color });
}

export function title(slide, ctx, text, kicker = "") {
  if (kicker) {
    ctx.addText(slide, { x: 64, y: 42, w: 720, h: 28, text: kicker, fontSize: 15, bold: true, color: C.blue });
  }
  ctx.addText(slide, {
    x: 64,
    y: kicker ? 76 : 54,
    w: 920,
    h: 62,
    text,
    fontSize: 34,
    bold: true,
    color: C.ink,
    face: ctx.fonts.title,
  });
}

export function footer(slide, ctx, n) {
  ctx.addText(slide, { x: 64, y: 680, w: 420, h: 18, text: "Multi-Agent Risk Assistant", fontSize: 11, color: "#64748b" });
  ctx.addText(slide, { x: 1170, y: 680, w: 45, h: 18, text: String(n).padStart(2, "0"), fontSize: 11, color: "#64748b", align: "right" });
}

export function pill(slide, ctx, x, y, w, text, fill = C.faint, color = C.ink) {
  ctx.addShape(slide, { x, y, w, h: 30, fill, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { x: x + 12, y: y + 7, w: w - 24, h: 16, text, fontSize: 12, bold: true, color, align: "center" });
}

export function node(slide, ctx, x, y, w, h, label, sub = "", fill = C.white, stroke = C.line) {
  ctx.addShape(slide, { x, y, w, h, fill, line: ctx.line(stroke, 1.2) });
  ctx.addText(slide, { x: x + 14, y: y + 12, w: w - 28, h: 24, text: label, fontSize: 17, bold: true, color: C.ink });
  if (sub) ctx.addText(slide, { x: x + 14, y: y + 42, w: w - 28, h: h - 48, text: sub, fontSize: 12, color: C.muted });
}

export function metric(slide, ctx, x, y, value, label, color = C.blue) {
  ctx.addText(slide, { x, y, w: 160, h: 40, text: value, fontSize: 32, bold: true, color });
  ctx.addText(slide, { x, y: y + 42, w: 180, h: 34, text: label, fontSize: 13, color: C.muted });
}

export function line(slide, ctx, x1, y1, x2, y2, color = C.line, width = 2) {
  const shape = slide.shapes.add({
    geometry: "line",
    position: { left: x1, top: y1, width: x2 - x1, height: y2 - y1 },
    line: { fill: color, width, style: "solid" },
    fill: "#00000000",
  });
  return shape;
}

export function arrow(slide, ctx, x1, y1, x2, y2, color = C.blue) {
  line(slide, ctx, x1, y1, x2, y2, color, 2.2);
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const len = 12;
  const a1 = angle + Math.PI * 0.82;
  const a2 = angle - Math.PI * 0.82;
  line(slide, ctx, x2, y2, x2 + Math.cos(a1) * len, y2 + Math.sin(a1) * len, color, 2.2);
  line(slide, ctx, x2, y2, x2 + Math.cos(a2) * len, y2 + Math.sin(a2) * len, color, 2.2);
}
