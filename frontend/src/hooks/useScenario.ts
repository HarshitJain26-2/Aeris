/**
 * useScenario hook
 *
 * Supports both:
 * - Mock mode (USE_MOCK === true): synchronous deterministic frontend ScenarioCalculator.
 * - Real API mode (USE_MOCK === false): async backend simulation via POST /api/scenario/simulate.
 *
 * State is shared globally across components through listener subscriptions.
 */
import { useState, useCallback, useEffect } from 'react';
import type { ScenarioInput, ScenarioResult } from '../types/scenario';
import type { AirQualityReading } from '../types/airQuality';
import { computeScenario } from '../lib/scenarioCalculator';
import { USE_MOCK, simulateScenario } from '../services/api';

interface ScenarioState {
  result: ScenarioResult | null;
  loading: boolean;
  error: string | null;
  run: (input: ScenarioInput, baseline: AirQualityReading) => Promise<void>;
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

  const run = useCallback(async (input: ScenarioInput, baseline: AirQualityReading) => {
    globalLoading = true;
    globalError = null;
    notify();
    try {
      if (USE_MOCK) {
        globalResult = computeScenario(input, baseline);
      } else {
        globalResult = await simulateScenario(input.trafficReductionPct, baseline);
      }
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
