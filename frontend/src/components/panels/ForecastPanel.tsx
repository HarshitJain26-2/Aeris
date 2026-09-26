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
    <Card accent="modelled" className="p-4 flex flex-col gap-3 shrink-0">
      <div className="flex justify-between items-start gap-2">
        <div>
          <h2 className="text-sm font-semibold text-text-primary mb-1 uppercase tracking-wide">
            PM2.5 Forecast ({horizonTitle})
          </h2>
          <ModelledTag label="1-HOUR MODEL ESTIMATE" />
        </div>
        {targetPoint && (
          <div className="text-right">
            <span className="text-xs text-text-muted">Target (t+1h)</span>
            <div className="font-mono text-base font-bold text-modelled">
              {targetPoint.pm25} <span className="text-xs font-normal text-text-muted">µg/m³</span>
            </div>
          </div>
        )}
      </div>

      <div className="mt-1">
        <ForecastChart data={chartPoints} loading={loading} error={!!error} onRetry={refetch} />
      </div>

      {/* Model Version and 90% Confidence Interval disclosure */}
      {targetPoint && (
        <div className="pt-2 border-t border-border flex flex-wrap justify-between items-center text-[10px] text-text-muted gap-1">
          <div className="flex items-center gap-1.5">
            <Activity size={11} className="text-modelled" />
            <span>Model: <span className="font-mono text-text-secondary">{data?.modelVersion || 'xgb-pm25-v1'}</span></span>
          </div>
          {targetPoint.pm25Lower != null && targetPoint.pm25Upper != null && (
            <span className="font-mono">
              90% CI: [{targetPoint.pm25Lower} – {targetPoint.pm25Upper} µg/m³]
            </span>
          )}
        </div>
      )}
    </Card>
  );
};
