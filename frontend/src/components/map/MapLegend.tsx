import React from 'react';
import { CPCB_BANDS } from '../../lib/cpcbAqi';

export const MapLegend: React.FC = () => {
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 'var(--space-4)',
        right: 'var(--space-4)',
        background: 'var(--color-bg-overlay)',
        backdropFilter: 'blur(12px)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: '10px 14px',
        boxShadow: 'var(--shadow-card)',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      }}
    >
      <p style={{ fontSize: '10px', color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        India CPCB AQI
      </p>
      <div style={{ display: 'flex', gap: '4px' }}>
        {CPCB_BANDS.map((band) => (
          <div
            key={band.band}
            title={`${band.label} (${band.aqiMin}-${band.aqiMax})`}
            style={{
              width: '16px',
              height: '6px',
              background: band.color,
              borderRadius: '2px',
              opacity: 0.9,
            }}
          />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
        <span>0 (Good)</span>
        <span>500+ (Severe)</span>
      </div>
    </div>
  );
};
