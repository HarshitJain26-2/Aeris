import React, { useState } from 'react';
import { Info, ChevronUp, ChevronDown } from 'lucide-react';

export const MapLegend: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(true);
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
        padding: '12px 14px',
        boxShadow: 'var(--shadow-card)',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        width: '290px',
        transition: 'all 200ms ease',
      }}
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Info size={13} style={{ color: 'var(--color-teal)' }} aria-hidden="true" />
          <p
            style={{
              fontSize: '11px',
              color: 'var(--color-text-primary)',
              fontWeight: 600,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              margin: 0,
            }}
          >
            Digital Twin Map Legend
          </p>
        </div>
        <button
          type="button"
          aria-label={isExpanded ? 'Collapse legend' : 'Expand legend'}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
          }}
        >
          {isExpanded ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
      </div>

      {/* PM2.5 Intensity Scale */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
          <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
            PM2.5 Intensity (µg/m³)
          </span>
          <span style={{ fontSize: '9px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
            CPCB NAQI
          </span>
        </div>
        <div
          style={{
            height: '7px',
            width: '100%',
            borderRadius: '4px',
            background:
              'linear-gradient(to right, #4ADE80, #FACC15, #FB923C, #EF4444, #991B1B)',
            marginBottom: '4px',
          }}
        />
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '9px',
            color: 'var(--color-text-secondary)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {labels.map((label, idx) => (
            <span
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              <div
                style={{
                  height: '3px',
                  width: '1px',
                  background: 'var(--color-border)',
                  marginBottom: '1px',
                  opacity: 0.8,
                }}
              />
              {label}
            </span>
          ))}
        </div>
      </div>

      {isExpanded && (
        <>
          <div style={{ height: '1px', background: 'var(--color-border)', opacity: 0.6 }} />

          {/* Spatial Map Elements */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Spatial Features
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '14px',
                    height: '10px',
                    border: '1.5px solid var(--color-teal)',
                    background: 'rgba(13, 148, 136, 0.25)',
                    borderRadius: '2px',
                    display: 'inline-block',
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>Urban Zone</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '14px',
                    height: '10px',
                    border: '2px solid #2dd4bf',
                    background: 'rgba(45, 212, 191, 0.45)',
                    borderRadius: '2px',
                    boxShadow: '0 0 6px rgba(45, 212, 191, 0.6)',
                    display: 'inline-block',
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>Selected Zone</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: '#FB923C',
                    border: '1.5px solid #1a1917',
                    display: 'inline-block',
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>Hotspot Point</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    fontSize: '9px',
                    padding: '1px 4px',
                    borderRadius: '2px',
                    background: 'var(--color-bg-elevated)',
                    border: '1px solid var(--color-border)',
                    color: 'var(--color-text-muted)',
                    fontFamily: 'var(--font-mono)',
                    lineHeight: '10px',
                  }}
                >
                  DEMO
                </span>
                <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>Demo Fixture</span>
              </div>
            </div>
          </div>

          <div style={{ height: '1px', background: 'var(--color-border)', opacity: 0.6 }} />

          {/* Provenance Semantics */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Data Provenance Language
            </span>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '14px',
                    height: '3px',
                    background: '#16a34a',
                    display: 'inline-block',
                    borderRadius: '1px',
                  }}
                />
                <span style={{ fontSize: '10px', color: 'var(--color-text-primary)' }}>Observed Sensor</span>
              </div>
              <span
                style={{
                  fontSize: '9px',
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-sm)',
                  background: '#2E9E5B',
                  color: '#FFFFFF',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                }}
              >
                Solid
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '14px',
                    height: '0px',
                    borderTop: '2px dashed #d97706',
                    display: 'inline-block',
                  }}
                />
                <span style={{ fontSize: '10px', color: 'var(--color-text-primary)' }}>Model Estimate / CAMS</span>
              </div>
              <span
                style={{
                  fontSize: '9px',
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px dashed #d97706',
                  color: '#d97706',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                }}
              >
                Dashed
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
