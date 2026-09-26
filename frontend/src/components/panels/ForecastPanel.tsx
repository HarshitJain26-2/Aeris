import React from 'react';
import { Card } from '../ui/Card';
import { ModelledTag } from '../status/ModelledTag';
import { useForecast } from '../../hooks/useForecast';
import { useAirQuality } from '../../hooks/useAirQuality';
import { ForecastChart } from '../charts/ForecastChart';
import type { ForecastPoint } from '../../types/forecast';
import { Activity } from 'lucide-react';

export const ForecastPanel: React.FC = () => {
  const { data, loading, error, refetch } = useForecast();
  const { data: airQuality } = useAirQuality();

  const horizonHours = data?.horizonHours ?? 1;
  const horizonTitle = horizonHours === 1 ? '1-Hour Ahead' : `${horizonHours}h Horizon`;

  // For genuine 1-hour-ahead model, connect current reading (t) to forecast (t+1h)
  const chartPoints: ForecastPoint[] = (!data?.points || data.points.length === 0)
    ? []
    : data.points.length === 1 && airQuality
    ? [
        {
          timestamp: airQuality.timestamp,
          pm25: airQuality.pm25,
          aqi: airQuality.aqi,
          aqiBand: airQuality.aqiBand,
          type: 'observed',
          dataSource: airQuality.dataSource,
        },
        data.points[0],
      ]
    : data.points;

  const targetPoint = data?.points?.find((p) => p.type === 'forecast') || data?.points?.[data.points.length - 1];

  return (
    <Card 
      accent="none" 
      className="shrink-0 flex flex-col gap-3"
      style={{
        background: '#FFFFFF',
        borderRadius: '14px',
        border: '1px solid #D9E2EC',
        boxShadow: '0 2px 4px rgba(11, 30, 61, 0.04)',
        padding: '16px'
      }}
    >
      <div className="flex justify-between items-start gap-2">
        <div>
          <h2 style={{ fontFamily: 'Inter, sans-serif', fontSize: '16px', fontWeight: 600, color: '#0B1F3A', margin: 0, marginBottom: '6px' }}>
            PM2.5 Forecast ({horizonTitle})
          </h2>
          <span style={{ 
            display: 'inline-block',
            background: '#EFF6FF', 
            color: '#075985', 
            border: '1px solid #60A5FA',
            padding: '2px 8px', 
            borderRadius: '4px',
            fontFamily: 'Inter, sans-serif', 
            fontSize: '12px', 
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            1-HOUR MODEL ESTIMATE
          </span>
        </div>
        {targetPoint && (
          <div className="text-right">
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#64748B' }}>Target (t+1h)</span>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'flex-end', gap: '4px' }}>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '24px', fontWeight: 700, color: '#0B2A4A', lineHeight: 1 }}>
                {targetPoint.pm25}
              </span>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 400, color: '#64748B' }}>
                µg/m³
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="mt-1">
        <ForecastChart data={chartPoints} loading={loading} error={!!error} onRetry={refetch} />
      </div>

      {/* Model Version and 90% Confidence Interval disclosure */}
      {targetPoint && (
        <div className="pt-2 border-t border-border flex flex-wrap justify-between items-center text-xs text-text-muted gap-1">
          <div className="flex items-center gap-2">
            <Activity size={11} className="text-modelled" />
            <span>Model: <span className="font-metric text-text-secondary">{data?.modelVersion || 'xgb-pm25-v1'}</span></span>
          </div>
          {targetPoint.pm25Lower != null && targetPoint.pm25Upper != null && (
            <span className="font-metric">
              90% CI: [{targetPoint.pm25Lower} – {targetPoint.pm25Upper} µg/m³]
            </span>
          )}
        </div>
      )}
    </Card>
  );
};
