import React from 'react';
import { Wind, MapPin, Clock } from 'lucide-react';

interface TopBarProps {
  lastUpdated?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ lastUpdated }) => {
  const timeStr = lastUpdated
    ? new Date(lastUpdated).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Kolkata',
      })
    : '—';

  return (
    <header
      style={{
        height: '52px',
        background: 'var(--color-bg-surface)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-6)',
        flexShrink: 0,
        zIndex: 10,
      }}
    >
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--color-teal), var(--color-teal-dim))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-teal)',
          }}
        >
          <Wind size={18} color="#fff" aria-hidden="true" />
        </div>
        <div>
          <h1
            style={{
              fontSize: 'var(--text-base)',
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              letterSpacing: '-0.01em',
              lineHeight: 1,
            }}
          >
            AERIS
          </h1>
          <p
            style={{
              fontSize: '0.65rem',
              color: 'var(--color-text-muted)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              lineHeight: 1,
              marginTop: '2px',
            }}
          >
            Urban Environmental Intelligence
          </p>
        </div>
      </div>

      {/* City + meta */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-text-secondary)' }}>
          <MapPin size={14} aria-hidden="true" />
          <span style={{ fontSize: 'var(--text-sm)', fontWeight: 500 }}>
            Pune, Maharashtra
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-text-muted)' }}>
          <Clock size={13} aria-hidden="true" />
          <span style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>
            {timeStr}
          </span>
        </div>
      </div>
    </header>
  );
};
