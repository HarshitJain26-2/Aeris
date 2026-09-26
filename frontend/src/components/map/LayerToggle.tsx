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
        padding: '4px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        background: '#FFFFFF',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(11, 30, 61, 0.08)',
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
          borderRadius: '6px',
          border: 'none',
          background: mode === 'observed' ? '#1769D2' : '#FFFFFF',
          color: mode === 'observed' ? '#FFFFFF' : '#475569',
          fontFamily: 'Inter, sans-serif',
          fontSize: '14px',
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 300ms ease',
        }}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-accent"
      >
        Observed
      </button>
      
      <button
        onClick={() => onChange('modelled')}
        style={{
          padding: '6px 12px',
          borderRadius: '6px',
          border: 'none',
          background: mode === 'modelled' ? '#1769D2' : '#FFFFFF',
          color: mode === 'modelled' ? '#FFFFFF' : '#475569',
          fontFamily: 'Inter, sans-serif',
          fontSize: '14px',
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 300ms ease',
        }}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-accent"
      >
        Model Estimate
      </button>
    </div>
  );
};
