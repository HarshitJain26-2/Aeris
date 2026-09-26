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
        background: '#FFFFFF',
        borderRadius: '12px',
        border: '1px solid #D9E2EC',
        boxShadow: '0 2px 8px rgba(11, 30, 61, 0.08)',
        padding: '16px',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        width: '300px',
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
              fontFamily: 'Inter, sans-serif',
              fontSize: '14px',
              color: '#0B1F3A',
              fontWeight: 600,
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
            color: 'var(--color-text-secondary)',
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
          <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#334155', fontWeight: 500 }}>
            PM2.5 Intensity (µg/m³)
          </span>
          <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#64748B', fontWeight: 400 }}>
            CPCB NAQI
          </span>
        </div>
        <div
          style={{
            height: '7px',
            width: '100%',
            borderRadius: '4px',
            background:
              'linear-gradient(to right, #22C55E, #FACC15, #F97316, #EF4444, #B91C1C)',
            marginBottom: '4px',
          }}
        />
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '12px',
            color: '#64748B',
            fontFamily: 'Inter, sans-serif',
            fontWeight: 400,
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
                  background: '#D9E2EC',
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
          <div style={{ height: '1px', background: '#D9E2EC', opacity: 0.6 }} />

          {/* Spatial Map Elements */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#334155', fontWeight: 500 }}>
              Spatial Features
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '14px',
                    height: '10px',
                    border: '1.5px solid #14B8A6',
                    background: 'rgba(13, 148, 136, 0.25)',
                    borderRadius: '2px',
                    display: 'inline-block',
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#64748B', fontWeight: 400 }}>Urban Zone</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '14px',
                    height: '10px',
                    border: '2px solid #14B8A6',
                    background: 'rgba(20, 184, 166, 0.2)',
                    borderRadius: '2px',
                    boxShadow: '0 0 6px rgba(20, 184, 166, 0.4)',
                    display: 'inline-block',
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#64748B', fontWeight: 400 }}>Selected Zone</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: '#F97316',
                    border: '1.5px solid #1a1917',
                    display: 'inline-block',
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#64748B', fontWeight: 400 }}>Hotspot Point</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    fontSize: '9px',
                    padding: '1px 4px',
                    borderRadius: '2px',
                    background: '#FFF7ED',
                    border: '1px solid #F97316',
                    color: '#C2410C',
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 500,
                    lineHeight: '10px',
                  }}
                >
                  DEMO
                </span>
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#64748B', fontWeight: 400 }}>Demo Fixture</span>
              </div>
            </div>
          </div>

          <div style={{ height: '1px', background: '#D9E2EC', opacity: 0.6 }} />

          {/* Provenance Semantics */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#334155', fontWeight: 500 }}>
              Data Provenance Language
            </span>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '14px',
                    height: '3px',
                    background: '#16A34A',
                    display: 'inline-block',
                    borderRadius: '1px',
                  }}
                />
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#64748B', fontWeight: 400 }}>Observed Sensor</span>
              </div>
              <span
                style={{
                  fontSize: '9px',
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-sm)',
                  background: '#16A34A',
                  color: '#FFFFFF',
                  fontFamily: 'Inter, sans-serif',
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
                    borderTop: '2px dashed #F59E0B',
                    display: 'inline-block',
                  }}
                />
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#64748B', fontWeight: 400 }}>Model Estimate / CAMS</span>
              </div>
              <span
                style={{
                  fontSize: '9px',
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid #F59E0B',
                  color: '#B45309',
                  background: '#FFFBEB',
                  fontFamily: 'Inter, sans-serif',
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
