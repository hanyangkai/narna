import { useEffect, useRef } from "react";

type Pt = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  c: number; // color index
};

const COUNT = 72;
const LINK = 140;
const MOUSE = 180;

const COLORS = [
  { r: 0, g: 220, b: 255 }, // cyan
  { r: 52, g: 211, b: 153 }, // lime
  { r: 167, g: 139, b: 250 }, // violet
  { r: 56, g: 189, b: 248 }, // sky
  { r: 244, g: 114, b: 182 }, // pink
];

export default function ParticleNetwork({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouse = useRef({ x: -9999, y: -9999, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let pts: Pt[] = [];

    function resize() {
      const parent = canvas!.parentElement;
      if (!parent) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = parent.clientWidth;
      const h = parent.clientHeight;
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      canvas!.style.width = `${w}px`;
      canvas!.style.height = `${h}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (!pts.length) {
        pts = Array.from({ length: COUNT }, () => ({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.45,
          vy: (Math.random() - 0.5) * 0.45,
          r: Math.random() * 1.8 + 0.9,
          c: Math.floor(Math.random() * COLORS.length),
        }));
      }
    }

    function draw() {
      const w = canvas!.clientWidth;
      const h = canvas!.clientHeight;
      ctx!.clearRect(0, 0, w, h);

      for (const p of pts) {
        if (mouse.current.active) {
          const dx = p.x - mouse.current.x;
          const dy = p.y - mouse.current.y;
          const dist = Math.hypot(dx, dy);
          if (dist < MOUSE && dist > 0) {
            const f = (MOUSE - dist) / MOUSE;
            p.vx += (dx / dist) * f * 0.05;
            p.vy += (dy / dist) * f * 0.05;
          }
        }
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.994;
        p.vy *= 0.994;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        p.x = Math.max(0, Math.min(w, p.x));
        p.y = Math.max(0, Math.min(h, p.y));
      }

      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const a = pts[i];
          const b = pts[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d = Math.hypot(dx, dy);
          if (d < LINK) {
            const alpha = (1 - d / LINK) * 0.45;
            const ca = COLORS[a.c];
            const cb = COLORS[b.c];
            const r = Math.round((ca.r + cb.r) / 2);
            const g = Math.round((ca.g + cb.g) / 2);
            const bl = Math.round((ca.b + cb.b) / 2);
            ctx!.strokeStyle = `rgba(${r}, ${g}, ${bl}, ${alpha})`;
            ctx!.lineWidth = 1.1;
            ctx!.beginPath();
            ctx!.moveTo(a.x, a.y);
            ctx!.lineTo(b.x, b.y);
            ctx!.stroke();
          }
        }
      }

      for (const p of pts) {
        const c = COLORS[p.c];
        ctx!.shadowBlur = 8;
        ctx!.shadowColor = `rgba(${c.r}, ${c.g}, ${c.b}, 0.8)`;
        ctx!.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.9)`;
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx!.fill();
      }
      ctx!.shadowBlur = 0;

      raf = requestAnimationFrame(draw);
    }

    const onMove = (e: MouseEvent) => {
      const rect = canvas!.getBoundingClientRect();
      mouse.current = { x: e.clientX - rect.left, y: e.clientY - rect.top, active: true };
    };
    const onLeave = () => {
      mouse.current.active = false;
    };

    resize();
    draw();
    window.addEventListener("resize", resize);
    canvas.addEventListener("mousemove", onMove);
    canvas.addEventListener("mouseleave", onLeave);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("mousemove", onMove);
      canvas.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={`fx-particles ${className}`.trim()}
      aria-hidden
    />
  );
}
