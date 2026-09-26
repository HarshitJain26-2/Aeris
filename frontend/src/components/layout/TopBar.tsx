import React from 'react';
import { Wind, MapPin, Clock, User } from 'lucide-react';
import { USE_MOCK } from '../../services/api';

interface TopBarProps {
  lastUpdated?: string;
  selectedZoneName?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ lastUpdated, selectedZoneName }) => {
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
        height: '64px',
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
      {/* Left section: Logo & Titles */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-card)',
          }}
        >
          <Wind size={20} color="#fff" aria-hidden="true" />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
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
            <span
              style={{
                fontSize: '0.7rem',
                color: 'var(--color-text-secondary)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                fontWeight: 600,
              }}
            >
              Urban Environmental Intelligence
            </span>
          </div>
          <p
            style={{
              fontSize: '0.7rem',
              color: 'var(--color-text-muted)',
              letterSpacing: '0.02em',
              lineHeight: 1,
            }}
          >
            Air Quality • Forecast • What-If Scenarios
          </p>
        </div>
      </div>

      {/* Right section: Pills & User */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        
        {/* Status Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Data Available Indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--aqi-good)', boxShadow: '0 0 0 2px var(--aqi-good-bg)' }} />
            <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--color-text-secondary)', letterSpacing: '0.05em' }}>
              DATA AVAILABLE
            </span>
          </div>

          <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
            Last updated: {lastUpdated ? timeStr : '10:45 AM'}
          </div>

          {/* Mode Badge (Live API vs Mock) */}
          {!USE_MOCK ? (
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '4px 10px',
              background: 'rgba(46, 158, 91, 0.15)',
              color: 'var(--color-observed)',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.65rem',
              fontWeight: 700,
              letterSpacing: '0.05em',
              border: '1px solid rgba(46, 158, 91, 0.3)'
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-observed)' }} />
              LIVE BACKEND · REAL ML
            </div>
          ) : (
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '4px 10px',
              background: 'var(--aqi-moderate-bg)',
              color: 'var(--aqi-moderate)',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.65rem',
              fontWeight: 700,
              letterSpacing: '0.05em',
              border: '1px solid rgba(214, 164, 0, 0.3)'
            }}>
              DEMO MODE · MOCK DATA
            </div>
          )}
        </div>

        {/* Location Pill */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '6px', 
          background: 'var(--color-bg-elevated)',
          padding: '6px 12px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--color-border)',
          color: 'var(--color-text-primary)' 
        }}>
          <MapPin size={14} color="var(--color-accent)" aria-hidden="true" />
          <span style={{ fontSize: 'var(--text-sm)', fontWeight: 500 }}>
            {selectedZoneName ? `Pune • ${selectedZoneName}` : 'Pune, Maharashtra'}
          </span>
        </div>

        {/* Clock */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-text-muted)' }}>
          <Clock size={14} aria-hidden="true" />
          <span style={{ fontSize: 'var(--text-sm)', fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
            {timeStr}
          </span>
        </div>
        
        {/* User Avatar Placeholder */}
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginLeft: '8px',
          color: 'var(--color-text-secondary)',
        }}>
          <User size={18} />
        </div>
      </div>
    </header>
  );
};
