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
import { AlertCircle } from 'lucide-react';

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
  const deltaColorClass = isZero
    ? 'text-text-secondary'
    : isReduction
    ? 'text-observed'
    : 'text-amber-500';
  const deltaSign = isZero ? '' : isReduction ? '-' : '+';

  return (
    <Card className="p-4 flex flex-col gap-5 flex-1 border-l-2 border-modelled relative min-w-0">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-sm font-semibold text-text-primary mb-1 uppercase tracking-wide">Digital Twin Simulation</h2>
          <ModelledTag label="MODEL ESTIMATE / COUNTERFACTUAL" />
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
          className="w-full"
        >
          Run Counterfactual Scenario
        </Button>
      </div>

      <div className="flex-1 flex flex-col justify-end">
        {error ? (
          <div className="min-h-[180px] flex items-center justify-center p-4 border border-dashed border-border rounded-lg">
            <ErrorState title="Scenario failed to compute" onRetry={handleRun} />
          </div>
        ) : loading ? (
          <div className="min-h-[180px] flex flex-col items-center justify-center text-center p-6 border border-dashed border-border rounded-lg gap-3">
            <Spinner size={24} color="var(--color-accent)" />
            <p className="text-sm font-medium text-text-secondary animate-pulse">
              Simulating XGBoost Counterfactual Scenario...
            </p>
          </div>
        ) : result ? (
          <div className="fade-in flex flex-col gap-3 mt-1">
            <div className="flex justify-between items-start">
              <div>
                <ModelledTag label="MODELLED — SCENARIO" />
                <p className="text-xs text-text-secondary mt-1">
                  Traffic reduction: <span className="font-semibold text-text-primary">{trafficReduction}%</span>
                </p>
              </div>
              <Button onClick={reset} className="text-xs py-1 px-3 bg-bg-elevated border border-border text-text-secondary hover:text-text-primary">
                Reset
              </Button>
            </div>
            
            <div className="grid grid-cols-2 gap-3 border-b border-border pb-3 mt-1">
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
                <p className="text-xs text-text-secondary mb-1">Scenario PM2.5</p>
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
                <p className="text-xs text-text-secondary mb-1">Absolute Delta</p>
                <span className={`text-sm font-mono font-semibold ${deltaColorClass}`}>
                  {deltaSign}<AnimatedNumber value={result.deltaAbsolute} /> µg/m³
                </span>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-secondary mb-1">Scenario Impact</p>
                <div className="flex items-baseline gap-1 justify-end">
                  <span className={`text-xl font-bold font-mono ${deltaColorClass}`}>
                    {deltaSign}<AnimatedNumber value={result.deltaPct} />%
                  </span>
                </div>
              </div>
            </div>
            
            <ScenarioCompare result={result} />

            {/* Scientific Provenance & Limitations */}
            {result.disclaimer && (
              <div className="flex items-start gap-2 p-2.5 rounded-lg bg-bg-elevated border border-border/70 text-[11px] text-text-secondary leading-relaxed mt-1">
                <AlertCircle size={14} className="text-modelled shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-text-primary">Scientific Limitation: </span>
                  {result.disclaimer}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="min-h-[180px] flex items-center justify-center text-center p-6 border border-dashed border-border rounded-lg">
            <EmptyState title="No scenario result" hint="Set traffic reduction (0–50%) and run counterfactual simulation" />
          </div>
        )}
      </div>
    </Card>
  );
};
