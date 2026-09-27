import React from 'react';
import { FlaskConical } from 'lucide-react';
import { USE_MOCK } from '../../services/api';

/**
 * DemoRibbon — persistent banner indicating mock data is active.
 * MUST be visible at all times during DEMO mode.
 * Helps prevent mock values from being mistaken for real data.
 */
export const DemoRibbon: React.FC = () => {
  if (!USE_MOCK) return null;

  return (
    <div
      role="banner"
    aria-label="Demo mode active — mock fixture data"
    style={{
      height: '28px',
      background: 'rgba(217,119,6,0.12)',
      borderBottom: '1px solid rgba(217,119,6,0.25)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '6px',
      color: 'var(--color-modelled)',
      fontSize: 'var(--text-xs)',
      fontWeight: 600,
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
      userSelect: 'none',
      flexShrink: 0,
    }}
  >
    <FlaskConical size={12} aria-hidden="true" />
    DEMO MODE · MOCK DATA
    </div>
  );
};
