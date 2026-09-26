import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { RangeSlider } from '../ui/RangeSlider';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { ScenarioCompare } from '../charts/ScenarioCompare';
import { useScenario } from '../../hooks/useScenario';
import { useAirQuality } from '../../hooks/useAirQuality';
import { useAnimatedNumber } from '../../hooks/useAnimatedNumber';

const AnimatedNumber = ({ value }: { value: number }) => {
  const animatedValue = useAnimatedNumber(value);
  return <>{animatedValue.toFixed(1)}</>;
};

export const ScenarioPanel: React.FC = () => {
  const [trafficReduction, setTrafficReduction] = useState(30);
  const { run, result, loading, error, reset } = useScenario();
  const { data: baseline } = useAirQuality();

  const handleRun = () => {
    run({ trafficReductionPct: trafficReduction }, baseline ?? null);
  };

  const isZero = result ? result.deltaAbsolute === 0 : false;
  const isReduction = result ? result.modelled.pm25 <= result.baseline.pm25 : true;
  const deltaSign = isZero ? '' : isReduction ? '-' : '+';

  return (
    <Card 
      accent="none"
      className="flex flex-col gap-4 flex-1 relative min-w-0"
      style={{
        background: '#FFFFFF',
        borderRadius: '14px',
        border: '1px solid #D9E2EC',
        boxShadow: '0 2px 4px rgba(11, 30, 61, 0.04)',
        padding: '20px'
      }}
    >
      <div className="flex justify-between items-start">
        <div>
          <h2 style={{ fontFamily: 'Inter, sans-serif', fontSize: '16px', fontWeight: 600, color: '#0B1F3A', margin: 0, marginBottom: '6px' }}>
            Digital Twin Simulation
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
            MODEL ESTIMATE / COUNTERFACTUAL
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <RangeSlider 
          label="Reduce Traffic Volume"
          value={trafficReduction}
          min={0}
          max={50}
          onChange={setTrafficReduction}
          disabled={loading}
        />
        
        <Button 
          onClick={handleRun} 
          loading={loading}
          disabled={loading}
          style={{
            background: '#155DA8',
            color: '#FFFFFF',
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
            fontWeight: 600,
            borderRadius: '6px',
            padding: '10px',
            border: 'none',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
          }}
          className="w-full"
        >
          Run Counterfactual Scenario
        </Button>
      </div>

      <div className="flex-1 flex flex-col justify-end">
        {error ? (
          <div className="min-h-[200px] flex items-center justify-center p-4 border border-dashed border-border rounded-lg">
            <ErrorState title="Scenario failed to compute" onRetry={handleRun} />
          </div>
        ) : loading ? (
          <div className="min-h-[200px] flex flex-col items-center justify-center text-center p-4 border border-dashed border-border rounded-lg gap-3">
            <Spinner size={24} color="var(--color-accent)" />
            <p className="text-sm font-medium text-text-secondary animate-pulse">
              Simulating XGBoost Counterfactual Scenario...
            </p>
          </div>
        ) : result ? (
          <div className="fade-in flex flex-col mt-1">
            {/* Divider from controls */}
            <div style={{ height: '1px', background: '#D9E2EC', margin: '8px 0 20px 0' }} />

            <div className="flex justify-between items-start">
              <div>
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
                  MODELLED — SCENARIO
                </span>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#475569', margin: '8px 0 0 0' }}>
                  Traffic reduction: <span style={{ fontWeight: 600, color: '#0B1F3A' }}>{trafficReduction}%</span>
                </p>
              </div>
              <button 
                onClick={reset} 
                style={{
                  background: '#F1F5F9',
                  color: '#475569',
                  border: '1px solid #D9E2EC',
                  fontFamily: 'Inter, sans-serif',
                  fontSize: '13px',
                  fontWeight: 500,
                  padding: '4px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = '#E2E8F0'}
                onMouseOut={(e) => e.currentTarget.style.background = '#F1F5F9'}
              >
                Reset
              </button>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '20px' }}>
              <div style={{ paddingBottom: '16px', borderBottom: '1px solid #D9E2EC' }}>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#475569', margin: '0 0 4px 0' }}>Baseline PM2.5</p>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                  <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '24px', fontWeight: 700, color: '#0B2A4A' }}>
                    <AnimatedNumber value={result.baseline.pm25} />
                  </span>
                  <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#475569' }}>µg/m³</span>
                </div>
              </div>
              <div style={{ paddingBottom: '16px', borderBottom: '1px solid #D9E2EC' }}>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#475569', margin: '0 0 4px 0' }}>Scenario PM2.5</p>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                  <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '24px', fontWeight: 700, color: '#0B2A4A' }}>
                    <AnimatedNumber value={result.modelled.pm25} />
                  </span>
                  <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#475569' }}>µg/m³</span>
                </div>
              </div>
              
              <div>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#475569', margin: '0 0 4px 0' }}>Absolute Delta</p>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                  <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '20px', fontWeight: 700, color: isReduction && !isZero ? '#15803D' : (isZero ? '#475569' : '#EF4444') }}>
                    {deltaSign}<AnimatedNumber value={result.deltaAbsolute} />
                  </span>
                  <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#475569' }}>µg/m³</span>
                </div>
              </div>
              <div>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#475569', margin: '0 0 4px 0' }}>Scenario Impact</p>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                  <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '20px', fontWeight: 700, color: isReduction && !isZero ? '#15803D' : (isZero ? '#475569' : '#EF4444') }}>
                    {deltaSign}<AnimatedNumber value={result.deltaPct} />%
                  </span>
                </div>
              </div>
            </div>
            
            <div style={{ marginTop: '20px' }}>
              <ScenarioCompare result={result} />
            </div>
          </div>
        ) : (
          <div className="min-h-[200px] flex items-center justify-center text-center p-4 border border-dashed border-border rounded-lg">
            <EmptyState title="No scenario result" hint="Set traffic reduction (0–50%) and run counterfactual simulation" />
          </div>
        )}
      </div>
    </Card>
  );
};
