import { useEffect, useRef, useState } from 'react';

export default function CountUp({ value = 0, duration = 800, decimals = 0, prefix = '', suffix = '' }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef({ start: 0, from: 0, to: value });
  useEffect(() => {
    ref.current.from = display;
    ref.current.to = value;
    ref.current.start = performance.now();
    let raf;
    const tick = (now) => {
      const elapsed = now - ref.current.start;
      const t = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(ref.current.from + (ref.current.to - ref.current.from) * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, duration]);
  return <span>{prefix}{display.toFixed(decimals)}{suffix}</span>;
}
