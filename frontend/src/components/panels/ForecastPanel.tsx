import React from 'react';
import { Card } from '../ui/Card';
import { ModelledTag } from '../status/ModelledTag';

import { useForecast } from '../../hooks/useForecast';
import { ForecastChart } from '../charts/ForecastChart';

export const ForecastPanel: React.FC = () => {
  const { data, loading, error, refetch } = useForecast();

  return (
    <Card className="p-4 flex flex-col gap-4 shrink-0">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-sm font-semibold text-text-primary mb-1 uppercase tracking-wide">PM2.5 Forecast (24h)</h2>
          <ModelledTag label="MODELLED — FORECAST" />
        </div>
      </div>
      
      <div className="mt-2">
        <ForecastChart data={data?.points || []} loading={loading} error={!!error} onRetry={refetch} />
      </div>
    </Card>
  );
};
