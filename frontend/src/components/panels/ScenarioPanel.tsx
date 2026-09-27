import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { ModelledTag } from '../status/ModelledTag';
import { RangeSlider } from '../ui/RangeSlider';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { ScenarioCompare } from '../charts/ScenarioCompare';
import { useScenario } from '../../hooks/useScenario';
import { useAirQuality } from '../../hooks/useAirQuality';
import { useAnimatedNumber } from '../../hooks/useAnimatedNumber';

const AnimatedNumber = ({ value, showPositiveSign = false }: { value: number; showPositiveSign?: boolean }) => {
  const animatedValue = useAnimatedNumber(value);
  const formatted = animatedValue.toFixed(1);
  if (formatted === '0.0' || formatted === '-0.0') {
    return <>0.0</>;
  }
  if (showPositiveSign && animatedValue > 0) {
    return <>+{formatted}</>;
  }
  return <>{formatted}</>;
};

export const ScenarioPanel: React.FC = () => {
  const [trafficReduction, setTrafficReduction] = useState(30);
  const [isSimulating, setIsSimulating] = useState(false);
  const { run, result, loading, error, reset } = useScenario();
  const { data: baseline } = useAirQuality();

  const signedDelta = result ? result.modelled.pm25 - result.baseline.pm25 : 0;
  const signedDeltaPct = result && result.baseline.pm25 !== 0
    ? ((result.modelled.pm25 - result.baseline.pm25) / result.baseline.pm25) * 100
    : 0;

  const handleRun = () => {
    if (baseline) {
      setIsSimulating(true);
      setTimeout(() => {
        run({ trafficReductionPct: trafficReduction }, baseline);
        setIsSimulating(false);
      }, 1000);
    }
  };

  return (
    <Card className="p-4 flex flex-col gap-6 flex-1 border-l-2 border-modelled relative min-w-0">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-sm font-semibold text-text-primary mb-1 uppercase tracking-wide">Digital Twin Simulation</h2>
          <ModelledTag label="Interactive Model" />
        </div>
      </div>

      <div className="flex flex-col gap-5">
        <RangeSlider 
          label="Reduce Traffic Volume"
          value={trafficReduction}
          min={0}
          max={50}
          onChange={setTrafficReduction}
          disabled={loading || !baseline}
        />
        
        <Button 
          onClick={handleRun} 
          loading={loading || isSimulating}
          disabled={!baseline || isSimulating}
          className="w-full"
        >
          Run Scenario
        </Button>
      </div>

      <div className="flex-1 flex flex-col justify-end">
        {error ? (
          <div className="h-[200px] flex items-center justify-center p-6 border border-dashed border-border rounded-lg">
            <ErrorState title="Scenario failed to compute" onRetry={handleRun} />
          </div>
        ) : isSimulating || loading ? (
          <div className="h-[200px] flex flex-col items-center justify-center text-center p-6 border border-dashed border-border rounded-lg gap-4">
            <Spinner size={24} color="var(--color-accent)" />
            <p className="text-sm font-medium text-text-secondary animate-pulse">
              Computing scenario...
            </p>
          </div>
        ) : result ? (
          <div className="fade-in flex flex-col gap-4 mt-2">
            <div className="flex justify-between items-start">
              <div>
                <ModelledTag label="MODELLED — SCENARIO" />
                <p className="text-xs text-text-secondary mt-2">Traffic reduced by {trafficReduction}%</p>
              </div>
              <Button onClick={reset} className="text-xs py-1 px-3 bg-bg-elevated border border-border text-text-secondary hover:text-text-primary">Reset</Button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 border-b border-border pb-4 mt-1">
              <div>
                <p className="text-xs text-text-secondary mb-1">Baseline PM2.5</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-medium text-text-primary">
                    <AnimatedNumber value={result.baseline.pm25} />
                  </span>
                  <span className="text-xs text-text-muted">µg/m³</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-secondary mb-1">Modelled PM2.5</p>
                <div className="flex items-baseline gap-1 justify-end">
                  <span className="text-lg font-mono font-bold text-modelled">
                    <AnimatedNumber value={result.modelled.pm25} />
                  </span>
                  <span className="text-xs text-text-muted">µg/m³</span>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between items-end">
              <div>
                <p className="text-xs text-text-secondary mb-1">Absolute Change</p>
                <span className="text-sm font-mono text-observed">
                  <AnimatedNumber value={signedDelta} showPositiveSign /> µg/m³
                </span>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-secondary mb-1">Projected Impact</p>
                <div className="flex items-baseline gap-1 justify-end">
                  <span className="text-2xl font-bold font-mono text-observed">
                    <AnimatedNumber value={signedDeltaPct} showPositiveSign />%
                  </span>
                </div>
              </div>
            </div>
            
            <ScenarioCompare result={result} />
            

          </div>
        ) : (
          <div className="h-[200px] flex items-center justify-center text-center p-6 border border-dashed border-border rounded-lg">
            <EmptyState title="No scenario result" hint="Run a scenario to see the projected outcome" />
          </div>
        )}
      </div>
    </Card>
  );
};
