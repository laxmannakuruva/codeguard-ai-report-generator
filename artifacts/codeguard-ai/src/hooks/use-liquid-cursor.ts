import { useEffect, useRef } from 'react';

import { GLOW_COLOR, GLOW_SIZE, DURATION_SLOW, EASING_FRIENDLY } from '@/lib/motion';

// A soft teal glow that follows the cursor with a smooth lag.
export function useLiquidCursor() {
  const glowRef = useRef<HTMLDivElement | null>(null);
  const targetRef = useRef({ x: 0, y: 0 });
  const currentRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;

    const glow = document.createElement('div');
    glow.setAttribute('data-cursor-glow', '');
    Object.assign(glow.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      width: GLOW_SIZE + 'px',
      height: GLOW_SIZE + 'px',
      borderRadius: '50%',
      background: 'radial-gradient(circle, ' + GLOW_COLOR + ' 0%, transparent 70%)',
      pointerEvents: 'none',
      transform: 'translate(-50%, -50%)',
      zIndex: '0',
      opacity: '0',
      transition: 'opacity ' + DURATION_SLOW + 'ms ' + EASING_FRIENDLY + ', transform ' + DURATION_SLOW + 'ms ' + EASING_FRIENDLY,
      willChange: 'transform, opacity',
    });
    document.body.appendChild(glow);
    glowRef.current = glow;

    const onMove = (e: MouseEvent) => {
      targetRef.current = { x: e.clientX, y: e.clientY };
      glow.style.opacity = '1';
    };
    window.addEventListener('mousemove', onMove, { passive: true });

    let raf = 0;
    const tick = () => {
      const t = targetRef.current;
      const c = currentRef.current;
      c.x += (t.x - c.x) * 0.15;
      c.y += (t.y - c.y) * 0.15;
      glow.style.transform = 'translate(' + c.x + 'px, ' + c.y + 'px) translate(-50%, -50%)';
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('mousemove', onMove);
      glow.remove();
    };
  }, []);
}
