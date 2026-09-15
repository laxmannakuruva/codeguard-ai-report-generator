import { useEffect, useState } from 'react';

const KEY = 'codeguard-welcomed';

export default function WelcomeOverlay() {
  const [visible, setVisible] = useState(false);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    if (sessionStorage.getItem(KEY)) return;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
      sessionStorage.setItem(KEY, '1');
      return;
    }
    setVisible(true);
    const fadeAt = setTimeout(() => setFading(true), 1200);
    const doneAt = setTimeout(() => {
      setVisible(false);
      sessionStorage.setItem(KEY, '1');
    }, 1800);
    return () => {
      clearTimeout(fadeAt);
      clearTimeout(doneAt);
    };
  }, []);

  if (!visible) return null;

  return (
    <div
      aria-hidden='true'
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f8faf6',
        pointerEvents: 'none',
        opacity: fading ? 0 : 1,
        transition: 'opacity 600ms cubic-bezier(0.2, 0.8, 0.2, 1)',
      }}
    >
      <div
        style={{
          textAlign: 'center',
          transform: fading ? 'translateY(-8px)' : 'translateY(0)',
          transition: 'transform 600ms cubic-bezier(0.2, 0.8, 0.2, 1)',
        }}
      >
        <div style={{ fontSize: 11, letterSpacing: '0.22em', textTransform: 'uppercase', color: '#4d907e', fontWeight: 700, marginBottom: 14 }}>
          Welcome to
        </div>
        <div style={{ fontSize: 42, fontWeight: 600, letterSpacing: '-0.04em', color: '#183f43', lineHeight: 1.1 }}>
          CodeGuard AI
        </div>
        <div style={{ marginTop: 10, fontSize: 14, color: '#687871' }}>
          AI-powered project report generator
        </div>
      </div>
    </div>
  );
}

