import React from 'react';
import { Card } from '../ui/Card';
import { ObservedTag } from '../status/ObservedTag';
import { AqiBadge } from '../ui/AqiBadge';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import { EmptyState } from '../ui/EmptyState';
import { useAirQuality } from '../../hooks/useAirQuality';
import { Thermometer, Droplets, Wind, Navigation } from 'lucide-react';

export const ObservedPanel: React.FC = () => {
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

  return (
    <Card accent="observed" className="p-4 flex flex-col gap-4 shrink-0">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-sm font-sans font-semibold text-text-primary mb-1 uppercase tracking-wide">{data.station}</h2>
          <ObservedTag />
        </div>
        {(!data.pm25 && !data.aqi) ? null : <AqiBadge aqi={data.aqi} band={data.aqiBand} size="lg" showPulse />}
      </div>

      {(!data.pm25 && !data.aqi) ? (
        <div className="flex-1 mt-4">
          <EmptyState title="No data available for this station" />
        </div>
      ) : (
        <>
          <div className="flex items-end gap-2 mt-2">
            <span className="text-3xl font-metric font-bold text-text-primary leading-none">
              {data.pm25}
            </span>
            <span className="text-sm text-text-muted mb-1">µg/m³ PM2.5</span>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-border">
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
