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
            Source Drivers
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
            MODEL ATTRIBUTION
          </span>
        </div>
      </div>

      {error ? (
        <div className="flex-1 mt-4">
          <ErrorState onRetry={refetch} />
        </div>
      ) : (
        <>
          <div className="flex items-center gap-4 mt-1 min-w-0">
            <DriverDonut drivers={data?.drivers || []} loading={loading} />
            <div className="flex-1 flex flex-col gap-3 min-w-0">
              {loading || !data ? (
                 <>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                   <div className="skeleton w-full h-4 rounded-md opacity-40"></div>
                 </>
              ) : data.drivers.length === 0 ? (
                <EmptyState title="Attribution data not yet available for this period" hint="Check back later." />
              ) : data.drivers.map((d) => {
                const CATEGORY_COLORS: Record<string, string> = {
                  'Traffic': '#F97316',
                  'Industrial': '#7C3AED',
                  'Residential/Biomass': '#14B8A6',
                };
                return (
                  <div key={d.category} className="flex justify-between items-center gap-2">
                    <div className="flex items-center gap-2 truncate">
                      <span 
                        className="w-2 h-2 rounded-full shrink-0" 
                        style={{ background: CATEGORY_COLORS[d.category] || 'var(--color-border)' }} 
                      />
                      <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 500, color: '#334155' }} className="truncate">{d.category}</span>
                    </div>
                    <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 600, color: '#0B1F3A' }} className="shrink-0">~{d.estimatedPct}%</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-1 pt-3 border-t border-border">
            <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 400, color: '#475569', margin: 0, lineHeight: 1.4 }} title="MODEL-ESTIMATED DRIVER / MODEL ATTRIBUTION">
              <span style={{ fontWeight: 600, color: '#334155' }}>MODEL-ESTIMATED DRIVER / MODEL ATTRIBUTION: </span>
              Feature importance estimates; not direct causal source apportionment.
            </p>
          </div>
        </>
      )}
    </Card>
  );
};
