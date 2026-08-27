import { useEffect, useRef } from "react";

const CHARS = "01NARNAADQA◇◆✦◈░▒▓█";
const COL_W = 18;
const SPEED = 0.55;

/** Soft matrix / data-stream rain for dark sections. */
export default function DataStream({ className = "", density = 0.55 }: { className?: string; density?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let cols: number[] = [];
    let colCount = 0;
    let h = 0;

    function resize() {
      const parent = canvas!.parentElement;
      if (!parent) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = parent.clientWidth;
      h = parent.clientHeight;
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      canvas!.style.width = `${w}px`;
      canvas!.style.height = `${h}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      colCount = Math.max(8, Math.floor((w / COL_W) * density));
      cols = Array.from({ length: colCount }, () => Math.random() * h);
    }

    function draw() {
      const w = canvas!.clientWidth;
      ctx!.fillStyle = "rgba(4, 16, 24, 0.12)";
      ctx!.fillRect(0, 0, w, h);

      ctx!.font = "11px 'IBM Plex Mono', monospace";
      for (let i = 0; i < colCount; i++) {
        const x = (i / colCount) * w + 4;
        const y = cols[i];
        const ch = CHARS[Math.floor(Math.random() * CHARS.length)];
        const hue = (i * 17 + y * 0.2) % 360;
        // teal-cyan-lime-magenta spectrum, biased cool
        const colors = [
          `rgba(0, 220, 255, 0.55)`,
          `rgba(52, 211, 153, 0.45)`,
          `rgba(167, 139, 250, 0.4)`,
          `rgba(56, 189, 248, 0.5)`,
          `rgba(250, 204, 21, 0.25)`,
        ];
        ctx!.fillStyle = colors[i % colors.length];
        if (Math.random() > 0.92) {
          ctx!.fillStyle = `hsla(${180 + (hue % 80)}, 90%, 65%, 0.85)`;
        }
        ctx!.fillText(ch, x, y);
        cols[i] += SPEED + (i % 5) * 0.15;
        if (cols[i] > h + 20) cols[i] = -Math.random() * 80;
      }

      raf = requestAnimationFrame(draw);
    }

    resize();
    draw();
    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [density]);

  return <canvas ref={canvasRef} className={`fx-datastream ${className}`.trim()} aria-hidden />;
}
