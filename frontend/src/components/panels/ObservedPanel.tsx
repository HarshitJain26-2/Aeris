import React from 'react';
import { Card } from '../ui/Card';
import { ObservedTag } from '../status/ObservedTag';
import { ModelledTag } from '../status/ModelledTag';
import { AqiBadge } from '../ui/AqiBadge';
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
    <Card accent={cardAccent} className="p-4 flex flex-col gap-3 shrink-0">
      <div className="flex justify-between items-start gap-2">
        <div className="min-w-0">
          <h2 className="text-sm font-sans font-semibold text-text-primary mb-1 uppercase tracking-wide truncate">
            {data.station}
          </h2>
          {isModelled ? (
            <ModelledTag label="MODEL ESTIMATE / MODELED" />
          ) : isObserved ? (
            <ObservedTag label="OBSERVED" />
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-bg-elevated border border-border text-amber-500 uppercase tracking-wide">
              Demo Fixture
            </span>
          )}
          <p className="text-[10px] text-text-muted mt-1">
            {isModelled
              ? 'CAMS Global PM2.5 • Atmospheric Model Estimate (Not ground station)'
              : isObserved
              ? 'Ground-station sensor telemetry'
              : 'Development baseline reference'}
          </p>
        </div>
        {(!data.pm25 && !data.aqi) ? null : <AqiBadge aqi={data.aqi} band={data.aqiBand} size="lg" showPulse />}
      </div>

      {/* Selected Zone Context if active */}
      {selectedEntity && selectedEntity.type === 'zone' && (
        <div className="flex items-center justify-between text-xs px-2.5 py-1.5 rounded bg-teal/10 border border-teal/20 text-teal">
          <div className="flex items-center gap-1.5 truncate">
            <MapPin size={12} className="shrink-0" />
            <span className="font-semibold truncate">Context: {selectedEntity.zone.name}</span>
          </div>
          <span className="text-[10px] text-text-secondary shrink-0 font-mono">
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
          <div className="flex items-end gap-2 mt-1">
            <span className="text-3xl font-metric font-bold text-text-primary leading-none">
              {data.pm25}
            </span>
            <span className="text-sm text-text-muted mb-1">µg/m³ PM2.5</span>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-2 pt-3 border-t border-border">
            <div className="flex items-center gap-2">
              <Thermometer size={14} className="text-text-muted" />
              <span className="text-sm font-mono">{data.temperatureC}°C</span>
            </div>
            <div className="flex items-center gap-2">
              <Droplets size={14} className="text-text-muted" />
              <span className="text-sm font-mono">{data.humidityPct}%</span>
            </div>
            <div className="flex items-center gap-2">
              <Wind size={14} className="text-text-muted" />
              <span className="text-sm font-mono">{data.windSpeedKmh} km/h</span>
            </div>
            <div className="flex items-center gap-2">
              <Navigation size={14} className="text-text-muted" />
              <span className="text-sm font-mono">T-Idx {data.trafficIndex}</span>
            </div>
          </div>
        </>
      )}
    </Card>
  );
};
