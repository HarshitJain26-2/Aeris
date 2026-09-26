import React from 'react';
import { Wind, LayoutDashboard, Map, CheckCircle } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { label: 'Dashboard', icon: <LayoutDashboard size={20} />, active: true },
    { label: 'Map', icon: <Map size={20} />, active: false },
    { label: 'Validate', icon: <CheckCircle size={20} />, active: false },
  ];

  return (
    <aside
      style={{
        width: '220px',
        background: 'var(--color-text-primary)',
        color: '#FFFFFF',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        borderRight: '1px solid var(--color-border)',
      }}
    >
      {/* Top Logo / Wordmark */}
      <div style={{ padding: 'var(--space-6)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Wind size={18} color="#fff" aria-hidden="true" />
        </div>
        <div>
          <h1
            style={{
              fontSize: 'var(--text-lg)',
              fontWeight: 700,
              color: '#FFFFFF',
              letterSpacing: '-0.01em',
              lineHeight: 1,
            }}
          >
            AERIS
          </h1>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '0 var(--space-4)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navItems.map((item) => (
          <a
            key={item.label}
            href={item.active ? '/' : '#'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 12px',
              borderRadius: 'var(--radius-md)',
              background: item.active ? 'rgba(255,255,255,0.1)' : 'transparent',
              color: item.active ? '#FFFFFF' : 'rgba(255,255,255,0.8)',
              textDecoration: 'none',
              fontWeight: 500,
              fontSize: 'var(--text-sm)',
              opacity: item.active ? 1 : 0.5,
              cursor: item.active ? 'pointer' : 'default',
              transition: 'all 300ms ease',
            }}
            className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-accent focus-visible:ring-offset-[#1a1a1a]"
            onClick={(e) => {
              if (!item.active) e.preventDefault();
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
              {item.icon}
              {item.label}
            </div>
          </a>
        ))}
      </nav>

      {/* Tagline */}
      <div style={{ padding: 'var(--space-6)', opacity: 0.7 }}>
        <p style={{ fontSize: '11px', color: '#FFFFFF', lineHeight: 1.4 }}>
          Cleaner Cities, <br /> Healthier Tomorrow
        </p>
      </div>
    </aside>
  );
};
