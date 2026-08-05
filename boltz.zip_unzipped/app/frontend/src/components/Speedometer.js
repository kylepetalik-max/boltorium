// Neon SVG speedometer for ride tracking
import { useEffect, useRef } from 'react';

export default function Speedometer({ speed = 0, max = 80, unit = 'km/h' }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.textContent = Math.round(speed);
  }, [speed]);

  const pct = Math.min(1, speed / max);
  const angle = -120 + pct * 240;
  const circ = 2 * Math.PI * 70;
  const offset = circ * (1 - pct);

  return (
    <div className="relative">
      <svg viewBox="0 0 180 180" className="w-44 h-44">
        <defs>
          <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1E90FF" />
            <stop offset="50%" stopColor="#FF33CC" />
            <stop offset="100%" stopColor="#FFD700" />
          </linearGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <circle cx="90" cy="90" r="70" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="10" />
        <circle cx="90" cy="90" r="70" fill="none" stroke="url(#sg)" strokeWidth="10" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          transform="rotate(150 90 90)" filter="url(#glow)"
          style={{ transition: 'stroke-dashoffset 0.4s ease' }} />
        <line x1="90" y1="90" x2="90" y2="40"
          stroke="#FF33CC" strokeWidth="3" strokeLinecap="round" filter="url(#glow)"
          transform={`rotate(${angle} 90 90)`}
          style={{ transition: 'transform 0.3s ease' }} />
        <circle cx="90" cy="90" r="6" fill="#FFD700" filter="url(#glow)" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span ref={ref} className="font-display font-black text-5xl gradient-text leading-none">0</span>
        <span className="font-display tracking-[0.3em] text-[10px] text-white/60 mt-1">{unit}</span>
      </div>
    </div>
  );
}
