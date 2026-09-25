import React from 'react';
import { Card } from '../ui/Card';
import { ModelledTag } from '../status/ModelledTag';
import { ErrorState } from '../ui/ErrorState';
import { useSourceAttribution } from '../../hooks/useSourceAttribution';
import { DriverDonut } from '../charts/DriverDonut';

export const DriverPanel: React.FC = () => {
  const { data, loading, error, refetch } = useSourceAttribution();

  return (
    <Card className="p-4 flex flex-col gap-4 shrink-0">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-sm font-semibold text-text-primary mb-1 uppercase tracking-wide">Model-Estimated Drivers</h2>
          <ModelledTag label="Model Estimate" />
        </div>
      </div>

      {error ? (
        <div className="flex-1 mt-4">
          <ErrorState onRetry={refetch} />
        </div>
      ) : (
        <>
          <div className="flex items-center gap-6 mt-2 min-w-0">
            <DriverDonut drivers={data?.drivers || []} loading={loading} />
            <div className="flex-1 flex flex-col gap-3 min-w-0">
              {loading || !data ? (
                 <>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                 </>
              ) : data.drivers.map((d, i) => (
                <div key={d.category} className="flex justify-between items-center gap-2">
                  <div className="flex items-center gap-2 truncate">
                    <span 
                      className="w-2 h-2 rounded-full shrink-0" 
                      style={{ background: `var(--chart-cat-${(i % 3) + 1})` }} 
                    />
                    <span className="text-sm font-medium text-text-primary">{d.category}</span>
                  </div>
                  <span className="text-sm font-mono text-text-secondary">~{d.estimatedPct}%</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-2 pt-3 border-t border-border">
            <p className="text-xs text-text-muted italic leading-relaxed" title="Model-estimated feature attribution; not direct causal source measurement.">
              Model-estimated feature attribution; not direct causal source measurement.
            </p>
          </div>
        </>
      )}
    </Card>
  );
};
