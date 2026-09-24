import React from 'react';
import type { HotspotFeature } from '../../types/hotspot';
import { AqiBadge } from '../ui/AqiBadge';
import { EmptyState } from '../ui/EmptyState';
import { Factory, Car, Home } from 'lucide-react';

interface ZonePopupProps {
  feature: HotspotFeature;
  onClose: () => void;
}

export const ZonePopup: React.FC<ZonePopupProps> = ({ feature, onClose }) => {
  const { name, aqi, aqiBand, pm25, dominantDriver } = feature.properties;

  const getDriverIcon = (driver: string) => {
    switch (driver) {
      case 'Traffic': return <Car size={14} />;
      case 'Industrial': return <Factory size={14} />;
      case 'Residential/Biomass': return <Home size={14} />;
      default: return null;
    }
  };

  return (
    <div
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        background: 'var(--color-bg-elevated)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-4)',
        boxShadow: 'var(--shadow-pop)',
        zIndex: 20,
        minWidth: '220px',
        pointerEvents: 'auto',
      }}
    >
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          background: 'transparent',
          border: 'none',
          color: 'var(--color-text-muted)',
          cursor: 'pointer',
          padding: '4px',
        }}
        aria-label="Close popup"
      >
        ✕
      </button>

      <div style={{ marginBottom: '12px' }}>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
          {name}
        </h3>
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
          Zone Analysis
        </p>
      </div>

      {(!pm25 && !aqi) ? (
        <EmptyState title="No data available for this station" />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>AQI</span>
            <AqiBadge aqi={aqi} band={aqiBand} size="sm" />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>PM2.5</span>
            <span style={{ fontSize: 'var(--text-sm)', fontFamily: 'var(--font-metric)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              {pm25} <span style={{ fontSize: '0.85em', color: 'var(--color-text-muted)', fontWeight: 400, fontFamily: 'var(--font-sans)' }}>µg/m³</span>
            </span>
          </div>

          <div style={{ height: '1px', background: 'var(--color-border)' }} />

          <div>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Model-Estimated Driver
            </span>
            <div style={{ 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: '5px', 
              padding: '3px 8px', 
              borderRadius: 'var(--radius-full)', 
              border: '1px dashed var(--color-modelled)', 
              color: 'var(--color-modelled)', 
              fontSize: 'var(--text-xs)', 
              fontWeight: 600, 
              letterSpacing: '0.04em', 
              textTransform: 'uppercase' 
            }}>
              {getDriverIcon(dominantDriver)}
              {dominantDriver}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
