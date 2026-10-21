"use client";

import { useEffect } from "react";

type SpringPoint = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  targetX: number;
  targetY: number;
  render: (x: number, y: number) => void;
};

const clamp = (value: number, min = -1, max = 1) => Math.min(max, Math.max(min, value));

/** Decorative motion only; the page and its links work without this enhancement. */
export default function LandingMotion() {
  useEffect(() => {
    const root = document.querySelector<HTMLElement>(".modern-home");
    if (!root) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    let disposeMotion: (() => void) | undefined;

    function configure() {
      disposeMotion?.();
      if (!root || reducedMotion.matches) return;

      const events = new AbortController();
      const points: SpringPoint[] = [];
      const transformed = new Set<HTMLElement>();
      const hero = root.querySelector<HTMLElement>(".modern-hero");
      const ribbonGroups = Array.from(root.querySelectorAll<HTMLElement>(".modern-hero__ribbons"));
      const final = root.querySelector<HTMLElement>(".modern-final");
      const signature = root.querySelector<HTMLElement>(".site-footer-signature");
      const workflow = root.querySelector<HTMLElement>(".modern-workflow");
      const routeLines = root.querySelector<SVGElement>(".modern-route-lines");
      const tiles = root.querySelector<HTMLElement>(".modern-tiles");
      const manifesto = root.querySelector<HTMLElement>(".modern-manifesto");
      const burst = root.querySelector<HTMLElement>(".modern-final__burst");
      let frame = 0;
      let lastTime = 0;
      let scrollDirty = true;
      let heroScroll = 0;
      let heroX = 0;
      let heroY = 0;

      function transform(element: HTMLElement, value: string) {
        transformed.add(element);
        element.style.transform = value;
      }

      function requestFrame() {
        if (!frame) frame = window.requestAnimationFrame(tick);
      }

      function addPointerSurface(scope: HTMLElement, render: SpringPoint["render"]) {
        if (!finePointer.matches) return;
        const point: SpringPoint = { x: 0, y: 0, vx: 0, vy: 0, targetX: 0, targetY: 0, render };
        points.push(point);
        scope.addEventListener("pointermove", (event) => {
          if (event.pointerType === "touch") return;
          const bounds = scope.getBoundingClientRect();
          point.targetX = clamp(((event.clientX - bounds.left) / bounds.width - 0.5) * 2);
          point.targetY = clamp(((event.clientY - bounds.top) / bounds.height - 0.5) * 2);
          requestFrame();
        }, { passive: true, signal: events.signal });
        const reset = () => {
          point.targetX = 0;
          point.targetY = 0;
          requestFrame();
        };
        scope.addEventListener("pointerleave", reset, { signal: events.signal });
        scope.addEventListener("pointercancel", reset, { signal: events.signal });
      }

      if (hero) addPointerSurface(hero, (x, y) => { heroX = x; heroY = y; });

      if (workflow && routeLines) addPointerSurface(workflow, (x, y) => {
        routeLines.style.transform = `translate3d(${x * 7}px, ${y * 5}px, 0)`;
      });

      root.querySelectorAll<HTMLElement>(".modern-feature__visual, .journey__visual, .modern-control__visual").forEach((scope) => {
        const sheet = scope.querySelector<HTMLElement>(".modern-feature__paper, .journey__document, .modern-review");
        const prompt = scope.querySelector<HTMLElement>(".modern-feature__prompt, .journey__prompt");
        addPointerSurface(scope, (x, y) => {
          if (sheet) transform(sheet, `perspective(1000px) rotateX(${-y * 3}deg) rotateY(${x * 4}deg) translate3d(${x * 3}px, ${y * 2}px, 0)`);
          if (prompt) transform(prompt, `translate3d(${x * -7}px, ${y * -5}px, 0) rotate(${-2 + x}deg)`);
        });
      });

      const signatureLogo = signature?.querySelector<HTMLElement>(".brand-lockup");
      if (signature && signatureLogo) addPointerSurface(signature, (x, y) => {
        transform(signatureLogo, `perspective(1400px) rotateX(${-y}deg) rotateY(${x * 1.5}deg)`);
      });

      if (final && burst) addPointerSurface(final, (x, y) => {
        burst.style.setProperty("--burst-x", `${x * 8}px`);
        burst.style.setProperty("--burst-y", `${y * 5}px`);
      });

      function readScroll() {
        if (hero) {
          const bounds = hero.getBoundingClientRect();
          heroScroll = clamp(-bounds.top / bounds.height, 0, 1);
        }
        scrollDirty = false;
      }

      function tick(time: number) {
        frame = 0;
        if (scrollDirty) readScroll();
        const dt = lastTime ? Math.min((time - lastTime) / 1000, 1 / 30) : 1 / 60;
        let moving = false;

        for (const point of points) {
          // Mass 1, stiffness 100, damping 10. Retarget from the current velocity.
          for (const axis of ["x", "y"] as const) {
            const velocity = axis === "x" ? "vx" : "vy";
            const target = axis === "x" ? point.targetX : point.targetY;
            point[velocity] += ((target - point[axis]) * 100 - point[velocity] * 10) * dt;
            point[axis] += point[velocity] * dt;
            if (Math.abs(target - point[axis]) < 0.001 && Math.abs(point[velocity]) < 0.001) {
              point[axis] = target;
              point[velocity] = 0;
            } else moving = true;
          }
          point.render(point.x, point.y);
        }

        for (const group of ribbonGroups) {
          Array.from(group.children).forEach((child, index) => {
            if (!(child instanceof HTMLElement)) return;
            const depth = (index + 1) * 3;
            transform(child, `translate3d(${heroX * depth - heroScroll * (18 + depth)}px, ${heroY * depth - heroScroll * 12}px, 0)`);
          });
        }
        lastTime = moving ? time : 0;
        if (moving) requestFrame();
      }

      const onScroll = () => { scrollDirty = true; requestFrame(); };
      window.addEventListener("scroll", onScroll, { passive: true, signal: events.signal });
      window.addEventListener("resize", onScroll, { passive: true, signal: events.signal });
      window.addEventListener("blur", () => {
        points.forEach((point) => { point.targetX = 0; point.targetY = 0; });
        requestFrame();
      }, { signal: events.signal });
      const resizeObserver = new ResizeObserver(onScroll);
      resizeObserver.observe(root);

      const revealObserver = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const target = entry.target as HTMLElement;
          if (target === signature) target.setAttribute("data-brand-visible", "");
          else if (target === tiles) target.setAttribute("data-tiles-visible", "");
          else if (target === manifesto) target.setAttribute("data-manifesto-visible", "");
          else if (target === burst) target.setAttribute("data-burst-visible", "");
          revealObserver.unobserve(entry.target);
        }
      }, { threshold: 0.15 });
      if (signature) revealObserver.observe(signature);
      if (tiles) revealObserver.observe(tiles);
      if (manifesto) revealObserver.observe(manifesto);
      if (burst) revealObserver.observe(burst);

      root.setAttribute("data-motion-ready", "");
      requestFrame();
      disposeMotion = () => {
        events.abort();
        window.cancelAnimationFrame(frame);
        resizeObserver.disconnect();
        revealObserver.disconnect();
        root.removeAttribute("data-motion-ready");
        signature?.removeAttribute("data-brand-visible");
        tiles?.removeAttribute("data-tiles-visible");
        manifesto?.removeAttribute("data-manifesto-visible");
        burst?.removeAttribute("data-burst-visible");
        routeLines?.style.removeProperty("transform");
        burst?.style.removeProperty("--burst-x");
        burst?.style.removeProperty("--burst-y");
        transformed.forEach((element) => element.style.removeProperty("transform"));
      };
    }

    configure();
    reducedMotion.addEventListener("change", configure);
    finePointer.addEventListener("change", configure);
    return () => {
      disposeMotion?.();
      reducedMotion.removeEventListener("change", configure);
      finePointer.removeEventListener("change", configure);
    };
  }, []);

  return null;
}
