import React from 'react';
import type { CpcbBand } from '../../types/airQuality';
import { getBandFromAqi } from '../../lib/cpcbAqi';

interface AqiBadgeProps {
  aqi: number;
  band?: CpcbBand;
  size?: 'sm' | 'md' | 'lg';
  showPulse?: boolean;
}

const sizeClasses = {
  sm: { badge: 'px-2 py-0.5 text-xs gap-1', dot: 'w-1.5 h-1.5' },
  md: { badge: 'px-3 py-1 text-sm gap-1.5', dot: 'w-2 h-2' },
  lg: { badge: 'px-4 py-2 text-base gap-2 font-semibold', dot: 'w-2.5 h-2.5' },
};

export const AqiBadge: React.FC<AqiBadgeProps> = ({
  aqi,
  band,
  size = 'md',
  showPulse = false,
}) => {
  const info = getBandFromAqi(aqi);
  const resolvedBand = band ?? info.band;
  const color = info.color;
  const sz = sizeClasses[size];

  return (
    <span
      role="status"
      aria-label={`India CPCB AQI: ${aqi} — ${resolvedBand}`}
      title={info.healthGuidance}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        borderRadius: 'var(--radius-full)',
        border: `1px solid ${color}40`,
        backgroundColor: `${color}18`,
        color: color,
        fontFamily: 'var(--font-sans)',
        fontWeight: 600,
        letterSpacing: '0.01em',
        userSelect: 'none',
      }}
      className={sz.badge}
    >
      <span
        style={{
          backgroundColor: color,
          borderRadius: '50%',
          flexShrink: 0,
          animation: showPulse ? 'aqi-pulse 2s ease-in-out infinite' : undefined,
        }}
        className={sz.dot}
        aria-hidden="true"
      />
      <span>{resolvedBand}</span>
      <span style={{ fontFamily: 'var(--font-mono)', opacity: 0.8 }}>{aqi}</span>
      <style>{`
        @keyframes aqi-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </span>
  );
};
