import React from 'react';
import { Card } from '../ui/Card';
import { ObservedTag } from '../status/ObservedTag';
import { ModelledTag } from '../status/ModelledTag';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import { EmptyState } from '../ui/EmptyState';
import { useAirQuality } from '../../hooks/useAirQuality';
import { Thermometer, Droplets, Wind, Navigation, MapPin } from 'lucide-react';
import type { SelectedMapEntity } from '../../types/zone';

interface ObservedPanelProps {
  selectedEntity?: SelectedMapEntity | null;
}

export const ObservedPanel: React.FC<ObservedPanelProps> = ({ selectedEntity }) => {
  const { data, loading, error, refetch } = useAirQuality();

  if (loading) {
    return (
      <Card className="p-4 flex flex-col gap-4 shrink-0">
        <div className="flex justify-between items-start">
          <div>
            <Skeleton width="120px" height="20px" style={{ marginBottom: '4px' }} />
            <Skeleton width="80px" height="24px" borderRadius="var(--radius-sm)" />
          </div>
          <Skeleton width="70px" height="34px" borderRadius="var(--radius-full)" />
        </div>
        <div className="flex items-end gap-2 mt-2">
          <Skeleton width="90px" height="40px" />
          <Skeleton width="80px" height="18px" style={{ marginBottom: '4px' }} />
        </div>
        <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-border">
          <Skeleton width="100%" height="20px" />
          <Skeleton width="100%" height="20px" />
          <Skeleton width="100%" height="20px" />
          <Skeleton width="100%" height="20px" />
        </div>
      </Card>
    );
  }
  if (error || !data) return <Card className="p-0 shrink-0"><ErrorState onRetry={refetch} /></Card>;

  const isModelled = data.dataSource === 'model_estimate';
  const isObserved = data.dataSource === 'observed';
  const cardAccent = isModelled ? 'modelled' : isObserved ? 'observed' : 'none';

  return (
    <Card 
      accent={cardAccent} 
      className="shrink-0 flex flex-col gap-3"
      style={{
        background: '#FFFFFF',
        borderRadius: '14px',
        border: '1px solid #D9E2EC',
        boxShadow: '0 2px 4px rgba(11, 30, 61, 0.04)',
        padding: '16px'
      }}
    >
      <div className="flex justify-between items-start gap-2" style={{ flexWrap: 'wrap' }}>
        <h2 style={{ fontFamily: 'Inter, sans-serif', fontSize: '15px', fontWeight: 600, color: '#0B1F3A', margin: 0, whiteSpace: 'normal', wordBreak: 'break-word' }}>
          {data.station}
        </h2>
        {(!data.pm25 && !data.aqi) ? null : (
          <span style={{ 
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            background: data.aqiBand === 'Poor' ? '#FFF7ED' : 'var(--aqi-poor-bg)', 
            color: data.aqiBand === 'Poor' ? '#C2410C' : 'var(--aqi-poor)', 
            border: data.aqiBand === 'Poor' ? '1px solid #FB923C' : '1px solid var(--aqi-poor)',
            padding: '4px 10px', borderRadius: '9999px',
            fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 600 
          }}>
             <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: data.aqiBand === 'Poor' ? '#C2410C' : 'var(--aqi-poor)' }} />
             {data.aqiBand} <span style={{ opacity: 0.8, fontFamily: 'var(--font-mono)' }}>{data.aqi}</span>
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div>
          {isModelled ? (
            <ModelledTag label="MODEL ESTIMATE / MODELED" />
          ) : isObserved ? (
            <ObservedTag label="OBSERVED" />
          ) : (
            <span 
              className="inline-flex items-center px-3 py-1 text-xs uppercase tracking-wide"
              style={{ background: '#FFF7ED', color: '#B45309', borderRadius: '4px', border: 'none', fontWeight: 600, fontFamily: 'Inter, sans-serif' }}
            >
              Demo Fixture
            </span>
          )}
        </div>
        <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: '#64748B', margin: 0 }}>
          {isModelled
            ? 'CAMS Global PM2.5 • Atmospheric Model Estimate (Not ground station)'
            : isObserved
            ? 'Ground-station sensor telemetry'
            : 'Development baseline reference'}
        </p>
      </div>

      {/* Selected Zone Context if active */}
      {selectedEntity && selectedEntity.type === 'zone' && (
        <div className="flex items-center justify-between text-xs px-4 py-2.5 rounded-lg bg-teal/10 border border-teal/20 text-teal">
          <div className="flex items-center gap-2 truncate">
            <MapPin size={12} className="shrink-0" />
            <span className="font-semibold truncate">Context: {selectedEntity.zone.name}</span>
          </div>
          <span className="text-xs text-text-secondary shrink-0 font-mono">
            {selectedEntity.zone.cameraCount} CCTV Feeds
          </span>
        </div>
      )}

      {(!data.pm25 && !data.aqi) ? (
        <div className="flex-1 mt-4">
          <EmptyState title="No data available for this station" />
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '4px' }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '28px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1 }}>
              {data.pm25}
            </span>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 400, color: '#334155' }}>
              µg/m³ PM2.5
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3" style={{ marginTop: '4px', paddingTop: '12px', borderTop: '1px solid #D9E2EC' }}>
            <div className="flex items-center gap-2">
              <Thermometer size={14} color="#64748B" />
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 500, color: '#334155' }}>{data.temperatureC}°C</span>
            </div>
            <div className="flex items-center gap-2">
              <Droplets size={14} color="#64748B" />
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 500, color: '#334155' }}>{data.humidityPct}%</span>
            </div>
            <div className="flex items-center gap-2">
              <Wind size={14} color="#64748B" />
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 500, color: '#334155' }}>{data.windSpeedKmh} km/h</span>
            </div>
            <div className="flex items-center gap-2">
              <Navigation size={14} color="#64748B" />
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 500, color: '#334155' }}>T-Idx {data.trafficIndex}</span>
            </div>
          </div>
        </>
      )}
    </Card>
  );
};
