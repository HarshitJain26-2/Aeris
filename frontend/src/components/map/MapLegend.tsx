import React from 'react';

export const MapLegend: React.FC = () => {
  const labels = ['0', '30', '60', '90', '120', '150+'];

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
        padding: '14px 16px',
        boxShadow: 'var(--shadow-card)',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        width: '280px',
      }}
    >
      <p style={{ fontSize: '11px', color: 'var(--color-text-primary)', fontWeight: 600, letterSpacing: '0.02em', margin: 0 }}>
        PM2.5 Intensity (µg/m³)
      </p>
      
      <div>
        <div 
          style={{
            height: '8px',
            width: '100%',
            borderRadius: '4px',
            background: 'linear-gradient(to right, var(--aqi-good), var(--aqi-moderate), var(--aqi-poor), var(--aqi-severe), var(--aqi-hazardous))',
            marginBottom: '4px'
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
          {labels.map((label, idx) => (
            <span key={idx} style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center' 
            }}>
              <div style={{ height: '4px', width: '1px', background: 'var(--color-border)', marginBottom: '2px', opacity: 0.8 }}></div>
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
