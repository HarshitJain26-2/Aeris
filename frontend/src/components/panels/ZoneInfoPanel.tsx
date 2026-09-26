import React from 'react';
import { Card } from '../ui/Card';
import { Camera, MapPin, Radio, Car, Factory, Home } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import type { SelectedMapEntity } from '../../types/zone';

interface ZoneInfoPanelProps {
  selectedEntity: SelectedMapEntity | null;
  mode?: 'observed' | 'modelled';
}

export const ZoneInfoPanel: React.FC<ZoneInfoPanelProps> = ({
  selectedEntity,
}) => {
  if (!selectedEntity) {
    return (
      <Card className="p-4 flex items-center justify-center min-h-[160px]">
        <EmptyState
          title="Select an Urban Zone or Hotspot"
          hint="Click on Alankar Chowk, Jehangir Chowk, RTO Chowk, or any hotspot point on the map to inspect verified coordinates, traffic streams, and provenance."
        />
      </Card>
    );
  }

  if (selectedEntity.type === 'zone') {
    const { zone, airshedPm25, airshedAqi, airshedBand, dataSource } = selectedEntity;

    const getBandStyles = (band: string | null | undefined) => {
      switch (band) {
        case 'Good': return { bg: '#F0FDF4', border: '#86EFAC', text: '#166534' };
        case 'Satisfactory': return { bg: '#FEFCE8', border: '#FDE047', text: '#854D0E' };
        case 'Moderate': return { bg: '#FFF7ED', border: '#FDBA74', text: '#9A3412' };
        case 'Poor': return { bg: '#FFF7ED', border: '#FB923C', text: '#C2410C' };
        case 'Very Poor': return { bg: '#FEF2F2', border: '#FCA5A5', text: '#991B1B' };
        case 'Severe': return { bg: '#FEF2F2', border: '#F87171', text: '#7F1D1D' };
        default: return { bg: '#F1F5F9', border: '#CBD5E1', text: '#475569' };
      }
    };
    
    const bandStyles = getBandStyles(airshedBand);

    return (
      <Card 
        accent="none"
        style={{
          background: '#FFFFFF',
          borderRadius: '14px',
          border: '1px solid #D9E2EC',
          boxShadow: '0 2px 4px rgba(11, 30, 61, 0.04)',
          padding: 0,
          overflow: 'hidden',
          width: '100%'
        }}
      >
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Header */}
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontFamily: 'Inter, sans-serif', fontSize: '18px', fontWeight: 700, color: '#0B1F3A', margin: 0 }}>
                  {zone.name}
                </h2>
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '11px', fontWeight: 500, color: '#1769D2', background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: '999px', padding: '4px 8px' }}>
                  {zone.zone_id}
                </span>
              </div>
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 400, color: '#475569', lineHeight: 1.4, margin: '4px 0 0 0' }}>
                {zone.description} • {zone.areaType}
              </p>
            </div>

            {dataSource === 'DEMO_FIXTURE' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 600, color: '#B45309', background: '#FFF7ED', border: '1px solid #F59E0B', borderRadius: '999px', padding: '5px 9px' }}>
                  DEMO FIXTURE
                </span>
              </div>
            )}
          </div>

          {/* Header Divider */}
          <div style={{ height: '1px', background: '#D9E2EC', width: '100%' }} />

          {/* Verified Fields Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* Coordinates Block */}
            <div style={{ background: '#FFFFFF', border: '1px solid #CBD5E1', borderRadius: '12px', padding: '16px', minHeight: '115px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <MapPin size={15} color="#1769D2" />
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 600, color: '#0B1F3A', textTransform: 'uppercase' }}>
                  COORDINATES
                </span>
              </div>
              <div style={{ fontFamily: 'Inter, sans-serif', fontSize: '19px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1 }}>
                {zone.latitude.toFixed(4)}° N, {zone.longitude.toFixed(4)}° E
              </div>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B' }}>
                WGS84 Junction Center
              </span>
            </div>

            {/* Traffic CCTV Feeds Block */}
            <div style={{ background: '#FFFFFF', border: '1px solid #CBD5E1', borderRadius: '12px', padding: '16px', minHeight: '115px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Camera size={15} color="#1769D2" />
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 600, color: '#0B1F3A', textTransform: 'uppercase' }}>
                  TRAFFIC CCTV FEEDS
                </span>
              </div>
              <div style={{ fontFamily: 'Inter, sans-serif', fontSize: '20px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1 }}>
                {zone.cameraCount} Streams
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '4px' }}>
                {zone.cameras.map((cam, idx) => (
                  <span key={idx} style={{ fontFamily: 'Inter, sans-serif', fontSize: '11px', fontWeight: 500, color: '#475569', background: '#F8FAFC', border: '1px solid #CBD5E1', borderRadius: '6px', padding: '3px 6px' }}>
                    {cam}
                  </span>
                ))}
              </div>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B' }}>
                Ground CCTV Vehicle Counts
              </span>
            </div>

            {/* Airshed PM2.5 Reference Block */}
            <div style={{ background: '#FFFFFF', border: '1px solid #CBD5E1', borderRadius: '12px', padding: '16px', minHeight: '115px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Radio size={15} color="#F59E0B" />
                <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 600, color: '#0B1F3A', textTransform: 'uppercase' }}>
                  AIRSHED PM2.5 REFERENCE
                </span>
              </div>
              
              {airshedPm25 != null ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                    <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '24px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1 }}>
                      {airshedPm25}
                    </span>
                    <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 400, color: '#475569' }}>
                      µg/m³
                    </span>
                  </div>
                  {airshedAqi != null && (
                    <span style={{ 
                      display: 'inline-flex', alignItems: 'center', gap: '4px',
                      background: bandStyles.bg, 
                      color: bandStyles.text, 
                      border: `1px solid ${bandStyles.border}`,
                      padding: '2px 8px', borderRadius: '999px',
                      fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 500 
                    }}>
                      {airshedBand} {airshedAqi}
                    </span>
                  )}
                </div>
              ) : (
                <div style={{ fontFamily: 'Inter, sans-serif', fontSize: '14px', fontWeight: 600, color: '#0B2A4A' }}>
                  City SAFAR Reference
                </div>
              )}
              
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }}>
                {zone.nearestStation} {zone.distanceToStationKm ? `(~${zone.distanceToStationKm} km)` : ''}
              </span>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // Hotspot feature selected
  const { name, locality, pm25, aqi, aqiBand, dominantDriver, latitude, longitude, dataSource } = selectedEntity;

  const getDriverIcon = (driver: string) => {
    switch (driver) {
      case 'Traffic': return <Car size={13} className="text-amber-500" />;
      case 'Industrial': return <Factory size={13} className="text-orange-500" />;
      case 'Residential/Biomass': return <Home size={13} className="text-teal" />;
      default: return null;
    }
  };

  return (
    <Card 
      accent="none"
      style={{
        background: '#FFFFFF',
        borderRadius: '14px',
        border: '1px solid #D9E2EC',
        boxShadow: '0 2px 4px rgba(11, 30, 61, 0.04)',
        padding: '16px'
      }}
    >
      <div className="flex flex-col gap-4">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-start gap-2">
          <div>
            <div className="flex items-baseline gap-2">
              <h2 style={{ fontFamily: 'Inter, sans-serif', fontSize: '16px', fontWeight: 600, color: '#0B1F3A', margin: 0 }}>
                {name}
              </h2>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B' }}>
                ({locality})
              </span>
            </div>
            <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B', margin: '4px 0 0 0' }}>
              Spatial Hotspot Telemetry Analysis
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span 
              className="px-3 py-1.5 rounded-xl uppercase tracking-wider"
              style={{ 
                background: 'rgba(245, 158, 11, 0.15)', 
                color: '#F59E0B', 
                border: '1px solid rgba(245, 158, 11, 0.3)',
                fontFamily: 'Inter, sans-serif',
                fontSize: '11px',
                fontWeight: 600
              }}
            >
              {dataSource === 'DEMO_FIXTURE' ? 'DEMO FIXTURE' : dataSource}
            </span>
          </div>
        </div>

        {/* Verified Fields Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* PM2.5 */}
          <div style={{ background: '#FFFFFF', border: '1px solid #D9E2EC', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 600, color: '#0B1F3A', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              PM2.5 INTENSITY
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '24px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1 }}>
                {pm25}
              </span>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B' }}>
                µg/m³
              </span>
            </div>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B' }}>
              Particulate Matter 2.5
            </span>
          </div>

          {/* AQI */}
          <div style={{ background: '#FFFFFF', border: '1px solid #D9E2EC', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 600, color: '#0B1F3A', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              INDIA NAQI
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', height: '24px' }}>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '24px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1 }}>
                {aqi}
              </span>
              <span style={{ 
                display: 'inline-flex', alignItems: 'center', gap: '4px',
                background: aqiBand === 'Poor' ? '#FFF7ED' : 'var(--aqi-poor-bg)', 
                color: aqiBand === 'Poor' ? '#C2410C' : 'var(--aqi-poor)', 
                border: aqiBand === 'Poor' ? '1px solid #FB923C' : '1px solid var(--aqi-poor)',
                padding: '2px 8px', borderRadius: '9999px',
                fontFamily: 'Inter, sans-serif', fontSize: '11px', fontWeight: 600 
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: aqiBand === 'Poor' ? '#C2410C' : 'var(--aqi-poor)' }} />
                {aqiBand}
              </span>
            </div>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B' }}>
              CPCB 6-Band Standard
            </span>
          </div>

          {/* Dominant Driver */}
          <div style={{ background: '#FFFFFF', border: '1px solid #D9E2EC', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 600, color: '#0B1F3A', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              DOMINANT DRIVER
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', height: '24px' }}>
              {getDriverIcon(dominantDriver)}
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '16px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1 }}>
                {dominantDriver}
              </span>
            </div>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B' }}>
              Source Attribution
            </span>
          </div>

          {/* Coordinates */}
          <div style={{ background: '#FFFFFF', border: '1px solid #D9E2EC', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 600, color: '#0B1F3A', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              COORDINATES
            </span>
            <div style={{ display: 'flex', alignItems: 'center', height: '24px' }}>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '15px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {latitude.toFixed(4)}° N, {longitude.toFixed(4)}° E
              </span>
            </div>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#64748B' }}>
              WGS84 Point Location
            </span>
          </div>
        </div>

      </div>
    </Card>
  );
};
