import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { ModelledTag } from '../status/ModelledTag';
import { RangeSlider } from '../ui/RangeSlider';
import { Button } from '../ui/Button';
import { ScenarioCompare } from '../charts/ScenarioCompare';
import { useScenario } from '../../hooks/useScenario';
import { useAirQuality } from '../../hooks/useAirQuality';

export const ScenarioPanel: React.FC = () => {
  const [trafficReduction, setTrafficReduction] = useState(30);
  const { run, result, loading } = useScenario();
  const { data: baseline } = useAirQuality();

  const handleRun = () => {
    if (baseline) {
      run({ trafficReductionPct: trafficReduction }, baseline);
    }
  };

  return (
    <Card className="p-4 flex flex-col gap-6 h-full border-l-2 border-modelled relative min-w-0">
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
          loading={loading}
          disabled={!baseline}
          className="w-full"
        >
          Run Scenario
        </Button>
      </div>

      <div className="flex-1 flex flex-col justify-end">
        {result ? (
          <div className="fade-in flex flex-col gap-4 mt-2">
            <div className="flex justify-between items-start">
              <div>
                <ModelledTag label="MODELLED — SCENARIO" />
                <p className="text-xs text-text-secondary mt-2">Traffic reduced by {trafficReduction}%</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 border-b border-border pb-4 mt-1">
              <div>
                <p className="text-xs text-text-secondary mb-1">Baseline PM2.5</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-medium text-text-primary">
                    {result.baseline.pm25}
                  </span>
                  <span className="text-xs text-text-muted">µg/m³</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-secondary mb-1">Modelled PM2.5</p>
                <div className="flex items-baseline gap-1 justify-end">
                  <span className="text-lg font-mono font-bold text-modelled">
                    {result.modelled.pm25}
                  </span>
                  <span className="text-xs text-text-muted">µg/m³</span>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between items-end">
              <div>
                <p className="text-xs text-text-secondary mb-1">Absolute Change</p>
                <span className="text-sm font-mono text-observed">
                  -{result.deltaAbsolute} µg/m³
                </span>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-secondary mb-1">Projected Impact</p>
                <div className="flex items-baseline gap-1 justify-end">
                  <span className="text-2xl font-bold font-mono text-observed">
                    -{result.deltaPct}%
                  </span>
                </div>
              </div>
            </div>
            
            <ScenarioCompare result={result} />
            
            <div className="p-3 bg-bg-elevated rounded-md border border-border mt-2">
              <p className="text-xs text-text-muted font-mono leading-relaxed opacity-80">
                // Deterministic frontend calc
                <br/>
                Δ = Baseline × (1 - {trafficReduction/100} × 0.40 × 0.80)
              </p>
            </div>
          </div>
        ) : (
          <div className="h-[200px] flex items-center justify-center text-center p-6 border border-dashed border-border rounded-lg">
            <p className="text-sm text-text-secondary">
              Adjust the slider and run a scenario to see the projected outcome.
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};
