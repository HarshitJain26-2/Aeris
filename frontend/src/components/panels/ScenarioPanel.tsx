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
import { Car, Factory, Trees, ShieldAlert, Cpu, Sparkles } from 'lucide-react';
import { USE_MOCK } from '../../services/api';

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

type InterventionCategory = 'traffic' | 'industrial' | 'biomass';

export const ScenarioPanel: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<InterventionCategory>('traffic');
  const [trafficReduction, setTrafficReduction] = useState(30);
  const { run, result, loading, error, reset } = useScenario();
  const { data: baseline } = useAirQuality();

  const signedDelta = result ? result.modelled.pm25 - result.baseline.pm25 : 0;
  const signedDeltaPct = result && result.baseline.pm25 !== 0
    ? ((result.modelled.pm25 - result.baseline.pm25) / result.baseline.pm25) * 100
    : 0;

  const handleRun = async () => {
    if (baseline) {
      await run({ trafficReductionPct: trafficReduction }, baseline);
    }
  };

  return (
    <Card className="p-4 flex flex-col gap-5 flex-1 border-l-2 border-modelled relative min-w-0 bg-white">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-sm font-semibold text-text-primary mb-1 uppercase tracking-wide">
            Digital Twin Scenario Simulation
          </h2>
          <div className="flex items-center gap-2 mt-1">
            <ModelledTag label="What-If Intervention" />
            <span className="text-[11px] px-2 py-0.5 rounded font-mono font-medium bg-slate-100 text-slate-700 border border-slate-200">
              {USE_MOCK ? 'Demo Mock Mode' : 'Backend ML Model'}
            </span>
          </div>
        </div>
      </div>

      {/* Intervention Action Category Selector (Scientifically Defensible Comparison) */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
          Intervention Category
        </label>
        <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-100/80 rounded-xl border border-border">
          <button
            type="button"
            onClick={() => setActiveCategory('traffic')}
            className={`flex flex-col items-center justify-center py-2 px-1 rounded-lg text-xs font-medium transition-all ${
              activeCategory === 'traffic'
                ? 'bg-white text-text-primary shadow-sm font-semibold border border-border/60'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Car size={14} className={activeCategory === 'traffic' ? 'text-amber-600' : 'text-text-muted'} />
              <span>Traffic</span>
            </div>
            <span className="text-[9px] text-emerald-600 font-mono mt-0.5 font-bold uppercase tracking-tight">
              Simulated
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveCategory('industrial')}
            className={`flex flex-col items-center justify-center py-2 px-1 rounded-lg text-xs font-medium transition-all ${
              activeCategory === 'industrial'
                ? 'bg-white text-text-primary shadow-sm font-semibold border border-border/60'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Factory size={14} className={activeCategory === 'industrial' ? 'text-orange-600' : 'text-text-muted'} />
              <span>Industrial</span>
            </div>
            <span className="text-[9px] text-text-muted font-mono mt-0.5 uppercase tracking-tight">
              Annual Context
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveCategory('biomass')}
            className={`flex flex-col items-center justify-center py-2 px-1 rounded-lg text-xs font-medium transition-all ${
              activeCategory === 'biomass'
                ? 'bg-white text-text-primary shadow-sm font-semibold border border-border/60'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Trees size={14} className={activeCategory === 'biomass' ? 'text-teal' : 'text-text-muted'} />
              <span>Biomass</span>
            </div>
            <span className="text-[9px] text-text-muted font-mono mt-0.5 uppercase tracking-tight">
              Unmonitored
            </span>
          </button>
        </div>
      </div>

      {/* Intervention Controls or Limitation Notice */}
      {activeCategory === 'traffic' ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <RangeSlider
              label="Traffic Volume Reduction"
              value={trafficReduction}
              min={0}
              max={50}
              step={5}
              onChange={setTrafficReduction}
              disabled={loading || !baseline}
            />
            {/* Quick Presets */}
            <div className="flex items-center justify-between gap-1 pt-1">
              <span className="text-[11px] text-text-muted">Presets:</span>
              <div className="flex items-center gap-1.5">
                {[0, 15, 30, 50].map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setTrafficReduction(preset)}
                    disabled={loading || !baseline}
                    className={`px-2 py-0.5 text-[11px] font-mono rounded border transition-colors ${
                      trafficReduction === preset
                        ? 'bg-blue-50 border-blue-300 text-blue-700 font-bold'
                        : 'bg-slate-50 border-slate-200 text-text-secondary hover:bg-slate-100'
                    }`}
                  >
                    {preset === 0 ? '0% (Base)' : `${preset}%`}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <Button
            onClick={handleRun}
            loading={loading}
            disabled={!baseline || loading}
            className="w-full flex items-center justify-center gap-2"
          >
            <Sparkles size={15} />
            <span>Simulate Modeled Outcome</span>
          </Button>
        </div>
      ) : activeCategory === 'industrial' ? (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-amber-700 font-semibold text-xs uppercase tracking-wide">
            <ShieldAlert size={15} />
            <span>Industrial Stack Emissions (Assumption-Based)</span>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed m-0">
            EDGAR v8.1 provides annual regional combustion context (1,329.56 Tonnes PM2.5 in Pune grid), but lacks diurnal hourly profiles. To avoid fabricating hourly values, industrial interventions are not simulated in the hourly ML model.
          </p>
          <span className="text-[11px] text-text-muted font-mono italic">
            Reference: docs/assumptions-limitations.md §3
          </span>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-teal font-semibold text-xs uppercase tracking-wide">
            <ShieldAlert size={15} />
            <span>Biomass & Dust Controls (Unmonitored)</span>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed m-0">
            Continuous hourly localized biomass burning and road dust suppression telemetry are not available in the current Round 1 sensor network. Marked for future sensor network expansion.
          </p>
          <span className="text-[11px] text-text-muted font-mono italic">
            Reference: docs/data-sources.md
          </span>
        </div>
      )}

      {/* Results / Empty / Loading / Error Section */}
      <div className="flex-1 flex flex-col justify-end pt-2 border-t border-border">
        {error ? (
          <div className="h-[210px] flex items-center justify-center p-4 border border-dashed border-red-200 rounded-xl bg-red-50/30">
            <ErrorState title="Scenario failed to compute" onRetry={handleRun} />
          </div>
        ) : loading ? (
          <div className="h-[210px] flex flex-col items-center justify-center text-center p-6 border border-dashed border-border rounded-xl gap-3 bg-slate-50/50">
            <Spinner size={26} color="var(--color-accent)" />
            <p className="text-xs font-semibold text-text-primary animate-pulse m-0">
              Evaluating XGBoost Counterfactual Scenario...
            </p>
            <span className="text-[11px] text-text-muted font-mono">
              Perturbing current-hour traffic volume ({trafficReduction}%)
            </span>
          </div>
        ) : result ? (
          <div className="flex flex-col gap-3">
            {/* Result Header & Solver Provenance */}
            <div className="flex justify-between items-start gap-2">
              <div>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-purple-50 text-purple-700 border border-purple-200">
                  MODELED SCENARIO — PREDICTIVE ESTIMATE
                </span>
                <p className="text-xs font-semibold text-text-primary mt-1 mb-0 flex items-center gap-1.5">
                  <Cpu size={12} className="text-teal" />
                  Traffic reduced by {result.input.trafficReductionPct}%
                </p>
              </div>
              <button
                type="button"
                onClick={reset}
                className="text-xs py-1 px-2.5 rounded-lg border border-border bg-slate-50 text-text-secondary hover:text-text-primary hover:bg-slate-100 transition-colors"
              >
                Reset
              </button>
            </div>

            {/* Baseline vs Scenario Numbers */}
            <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-50/80 border border-border">
              <div>
                <span className="text-[11px] text-text-muted uppercase font-medium">Baseline PM2.5</span>
                <div className="flex items-baseline gap-1 mt-0.5">
                  <span className="text-lg font-mono font-bold text-text-primary">
                    <AnimatedNumber value={result.baseline.pm25} />
                  </span>
                  <span className="text-xs text-text-muted">µg/m³</span>
                </div>
                <span className="text-[10px] text-text-muted">
                  AQI: {result.baseline.aqi} ({result.baseline.aqiBand})
                </span>
              </div>

              <div className="text-right">
                <span className="text-[11px] text-text-muted uppercase font-medium">Modelled PM2.5</span>
                <div className="flex items-baseline gap-1 justify-end mt-0.5">
                  <span className="text-lg font-mono font-bold text-teal">
                    <AnimatedNumber value={result.modelled.pm25} />
                  </span>
                  <span className="text-xs text-text-muted">µg/m³</span>
                </div>
                <span className="text-[10px] text-text-muted">
                  AQI: {result.modelled.aqi} ({result.modelled.aqiBand})
                </span>
              </div>
            </div>

            {/* Impact Metric Summary */}
            <div className="flex justify-between items-center px-1">
              <div>
                <span className="text-[11px] text-text-muted block">Absolute Delta</span>
                <span className={`text-sm font-mono font-bold ${signedDelta <= 0 ? 'text-emerald-700' : 'text-amber-700'}`}>
                  <AnimatedNumber value={signedDelta} showPositiveSign /> µg/m³
                </span>
              </div>
              <div className="text-right">
                <span className="text-[11px] text-text-muted block">Modelled Impact</span>
                <span className={`text-base font-bold font-mono ${signedDeltaPct <= 0 ? 'text-emerald-700' : 'text-amber-700'}`}>
                  <AnimatedNumber value={signedDeltaPct} showPositiveSign />%
                </span>
              </div>
            </div>

            {/* Bar Chart Comparison */}
            <ScenarioCompare result={result} />

            {/* Scientific Limitation Disclosure */}
            <div className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-200/70 text-[11px] text-amber-950 leading-relaxed">
              <span className="font-semibold">Scientific Disclosure: </span>
              {result.disclaimer}
            </div>
          </div>
        ) : (
          <div className="h-[200px] flex items-center justify-center text-center p-4 border border-dashed border-border rounded-xl">
            <EmptyState
              title="No scenario simulated"
              hint="Adjust traffic reduction percentage (0–50%) and click Simulate to evaluate modeled outcome."
            />
          </div>
        )}
      </div>
    </Card>
  );
};
