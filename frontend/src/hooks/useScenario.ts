import { useState, useCallback, useEffect } from 'react';
import type { ScenarioInput, ScenarioResult } from '../types/scenario';
import type { AirQualityReading } from '../types/airQuality';
import { simulateScenario } from '../services/api';

interface ScenarioState {
  result: ScenarioResult | null;
  loading: boolean;
  error: string | null;
  run: (input: ScenarioInput, baseline?: AirQualityReading | null) => Promise<void>;
  reset: () => void;
}

let globalResult: ScenarioResult | null = null;
let globalLoading = false;
let globalError: string | null = null;
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach(l => l());
}

export function useScenario(): ScenarioState {
  const [state, setState] = useState({ result: globalResult, loading: globalLoading, error: globalError });

  useEffect(() => {
    const handler = () => setState({ result: globalResult, loading: globalLoading, error: globalError });
    listeners.add(handler);
    return () => { listeners.delete(handler); };
  }, []);

  const run = useCallback(async (input: ScenarioInput, baseline?: AirQualityReading | null) => {
    globalLoading = true;
    globalError = null;
    notify();
    try {
      globalResult = await simulateScenario(input.trafficReductionPct, baseline || undefined);
    } catch (err) {
      globalError = err instanceof Error ? err.message : 'Calculation failed';
    } finally {
      globalLoading = false;
      notify();
    }
  }, []);

  const reset = useCallback(() => {
    globalResult = null;
    globalError = null;
    notify();
  }, []);

  return { result: state.result, loading: state.loading, error: state.error, run, reset };
}
