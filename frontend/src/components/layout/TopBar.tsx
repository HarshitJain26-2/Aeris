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
        background: '#FFFFFF',
        borderBottom: '1px solid #D9E2EC',
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
                fontFamily: 'Inter, sans-serif',
                fontSize: '18px',
                fontWeight: 700,
                color: '#0B1F3A',
                lineHeight: 1,
              }}
            >
              AERIS
            </h1>
            <span
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: '12px',
                fontWeight: 600,
                color: '#64748B',
                textTransform: 'uppercase',
              }}
            >
              Urban Environmental Intelligence
            </span>
          </div>
          <p
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: '12px',
              fontWeight: 400,
              color: '#64748B',
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
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#16A34A' }} />
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 500, color: '#15803D' }}>
              DATA AVAILABLE
            </span>
          </div>

          <div style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 400, color: '#64748B' }}>
            Last updated: {lastUpdated ? timeStr : '10:45 AM'}
          </div>

          {/* Mode Badge (Live API vs Mock) */}
          {!USE_MOCK ? (
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '6px 12px',
              boxShadow: '0 2px 4px rgba(11, 30, 61, 0.05)',
              background: 'rgba(46, 158, 91, 0.15)',
              color: 'var(--color-observed)',
              borderRadius: 'var(--radius-full)',
              fontFamily: 'Inter, sans-serif',
              fontSize: '12px',
              fontWeight: 600,
              border: '1px solid rgba(46, 158, 91, 0.3)'
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-observed)' }} />
              LIVE BACKEND · REAL ML
            </div>
          ) : (
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '6px 12px',
              background: '#FEF3C7',
              color: '#B45309',
              borderRadius: 'var(--radius-full)',
              fontFamily: 'Inter, sans-serif',
              fontSize: '12px',
              fontWeight: 600,
              border: '1px solid #F59E0B'
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
          background: '#F8FAFC',
          padding: '6px 12px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--color-border)',
          color: '#0B1F3A' 
        }}>
          <MapPin size={14} color="var(--color-accent)" aria-hidden="true" />
          <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '14px', fontWeight: 500 }}>
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
