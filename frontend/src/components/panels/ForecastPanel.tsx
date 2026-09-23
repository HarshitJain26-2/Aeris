import React from 'react';
import { Card } from '../ui/Card';
import { ModelledTag } from '../status/ModelledTag';
import { SkeletonPanel } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import { useForecast } from '../../hooks/useForecast';
import { ForecastChart } from '../charts/ForecastChart';

export const ForecastPanel: React.FC = () => {
  const { data, loading, error, refetch } = useForecast();

  if (loading) return <Card className="p-4"><SkeletonPanel rows={4} /></Card>;
  if (error || !data) return <Card className="p-0 h-full"><ErrorState onRetry={refetch} /></Card>;

  return (
    <Card className="p-4 flex flex-col gap-4">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-sm font-semibold text-text-primary mb-1 uppercase tracking-wide">PM2.5 Forecast (24h)</h2>
          <ModelledTag label="MODELLED — FORECAST" />
        </div>
      </div>
      
      <div className="mt-2">
        <ForecastChart data={data.points} />
      </div>
    </Card>
  );
};
