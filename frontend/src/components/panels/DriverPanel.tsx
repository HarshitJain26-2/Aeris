import React from 'react';
import { Card } from '../ui/Card';
import { ModelledTag } from '../status/ModelledTag';
import { ErrorState } from '../ui/ErrorState';
import { EmptyState } from '../ui/EmptyState';
import { useSourceAttribution } from '../../hooks/useSourceAttribution';
import { DriverDonut } from '../charts/DriverDonut';

export const DriverPanel: React.FC = () => {
  const { data, loading, error, refetch } = useSourceAttribution();

  return (
    <Card accent="modelled" className="p-4 flex flex-col gap-3 shrink-0">
      <div className="flex justify-between items-start gap-2">
        <div>
          <h2 className="text-sm font-semibold text-text-primary mb-1 uppercase tracking-wide">
            Source Drivers
          </h2>
          <ModelledTag label="MODEL ATTRIBUTION" />
        </div>
      </div>

      {error ? (
        <div className="flex-1 mt-4">
          <ErrorState onRetry={refetch} />
        </div>
      ) : (
        <>
          <div className="flex items-center gap-6 mt-1 min-w-0">
            <DriverDonut drivers={data?.drivers || []} loading={loading} />
            <div className="flex-1 flex flex-col gap-2.5 min-w-0">
              {loading || !data ? (
                 <>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                 </>
              ) : data.drivers.length === 0 ? (
                <EmptyState title="Attribution data not yet available for this period" hint="Check back later." />
              ) : data.drivers.map((d, i) => (
                <div key={d.category} className="flex justify-between items-center gap-2">
                  <div className="flex items-center gap-2 truncate">
                    <span 
                      className="w-2 h-2 rounded-full shrink-0" 
                      style={{ background: `var(--chart-cat-${(i % 3) + 1})` }} 
                    />
                    <span className="text-sm font-medium text-text-primary truncate">{d.category}</span>
                  </div>
                  <span className="text-xs font-mono font-semibold text-text-secondary shrink-0">~{d.estimatedPct}%</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-1 pt-2.5 border-t border-border">
            <p className="text-[11px] text-text-muted leading-relaxed" title="MODEL-ESTIMATED DRIVER / MODEL ATTRIBUTION">
              <span className="font-semibold text-text-secondary">MODEL-ESTIMATED DRIVER / MODEL ATTRIBUTION: </span>
              Feature importance estimates; not direct causal source apportionment.
            </p>
          </div>
        </>
      )}
    </Card>
  );
};
