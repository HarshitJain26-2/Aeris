import React from 'react';
import { MapPin, Crosshair } from 'lucide-react';
import type { UrbanZone, SelectedMapEntity } from '../../types/zone';

interface ZoneSelectorProps {
  zones: UrbanZone[];
  selectedEntity: SelectedMapEntity | null;
  onSelectZone: (zone: UrbanZone | null) => void;
}

export const ZoneSelector: React.FC<ZoneSelectorProps> = ({
  zones,
  selectedEntity,
  onSelectZone,
}) => {
  const activeZoneId =
    selectedEntity && selectedEntity.type === 'zone'
      ? selectedEntity.zone.zone_id
      : null;

  return (
    <div
      role="toolbar"
      aria-label="Zone selection toolbar"
      style={{
        position: 'absolute',
        top: 'var(--space-4)',
        right: 'var(--space-4)',
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
        maxWidth: 'calc(100% - 32px)',
        overflowX: 'auto',
      }}
    >
      <button
        type="button"
        onClick={() => onSelectZone(null)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 10px',
          borderRadius: 'var(--radius-md)',
          border: 'none',
          background: activeZoneId === null ? '#E2E8F0' : 'transparent',
          color: activeZoneId === null ? '#0B1F3A' : '#475569',
          fontFamily: 'Inter, sans-serif',
          fontSize: '13px',
          fontWeight: activeZoneId === null ? 600 : 500,
          cursor: 'pointer',
          transition: 'all 150ms ease',
          whiteSpace: 'nowrap',
        }}
        title="View all Pune monitoring zones"
      >
        <Crosshair size={13} aria-hidden="true" />
        <span>All Pune</span>
      </button>

      <div style={{ width: '1px', height: '18px', background: 'var(--color-border)', margin: '0 2px' }} />

      {zones.map((zone) => {
        const isSelected = activeZoneId === zone.zone_id;
        return (
          <button
            key={zone.zone_id}
            type="button"
            onClick={() => onSelectZone(zone)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 10px',
              borderRadius: 'var(--radius-md)',
              border: isSelected ? '1px solid var(--color-teal)' : '1px solid transparent',
              background: isSelected ? 'rgba(20, 184, 166, 0.15)' : 'transparent',
              color: isSelected ? '#0D9488' : '#475569',
              fontFamily: 'Inter, sans-serif',
              fontSize: '13px',
              fontWeight: isSelected ? 600 : 500,
              cursor: 'pointer',
              transition: 'all 150ms ease',
              whiteSpace: 'nowrap',
            }}
            title={`${zone.name} - ${zone.cameraCount} CCTV cameras`}
          >
            <MapPin size={12} color={isSelected ? '#14B8A6' : '#94A3B8'} aria-hidden="true" />
            <span>{zone.name}</span>
            <span
              style={{
                fontSize: '11px',
                padding: '2px 6px',
                borderRadius: 'var(--radius-sm)',
                background: isSelected ? '#14B8A6' : '#F1F5F9',
                color: isSelected ? '#FFFFFF' : '#64748B',
                fontFamily: 'Inter, sans-serif',
                fontWeight: 500,
              }}
            >
              {zone.cameraCount} cam
            </span>
          </button>
        );
      })}
    </div>
  );
};
