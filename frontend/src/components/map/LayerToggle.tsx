import React from 'react';
import { Layers } from 'lucide-react';

interface LayerToggleProps {
  mode: 'observed' | 'modelled';
  onChange: (mode: 'observed' | 'modelled') => void;
}

export const LayerToggle: React.FC<LayerToggleProps> = ({ mode, onChange }) => {
  return (
    <div
      style={{
        position: 'absolute',
        top: 'var(--space-4)',
        left: 'var(--space-4)',
        background: 'var(--color-bg-overlay)',
        backdropFilter: 'blur(12px)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-1)',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        boxShadow: 'var(--shadow-card)',
        zIndex: 10,
      }}
    >
      <div style={{ padding: '0 8px', color: 'var(--color-text-muted)' }}>
        <Layers size={14} aria-hidden="true" />
      </div>
      
      <button
        onClick={() => onChange('observed')}
        style={{
          padding: '6px 12px',
          borderRadius: 'var(--radius-md)',
          border: 'none',
          background: mode === 'observed' ? 'var(--color-bg-elevated)' : 'transparent',
          color: mode === 'observed' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
          fontSize: 'var(--text-xs)',
          fontWeight: mode === 'observed' ? 600 : 500,
          cursor: 'pointer',
          transition: 'all 200ms ease',
        }}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-accent"
      >
        Observed
      </button>
      
      <button
        onClick={() => onChange('modelled')}
        style={{
          padding: '6px 12px',
          borderRadius: 'var(--radius-md)',
          border: 'none',
          background: mode === 'modelled' ? 'var(--color-modelled-bg)' : 'transparent',
          color: mode === 'modelled' ? 'var(--color-modelled)' : 'var(--color-text-secondary)',
          fontSize: 'var(--text-xs)',
          fontWeight: mode === 'modelled' ? 600 : 500,
          cursor: 'pointer',
          transition: 'all 200ms ease',
        }}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-accent"
      >
        Model Estimate
      </button>
    </div>
  );
};
