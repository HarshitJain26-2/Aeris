/**
 * useScenario hook
 *
 * Round 1: calls the deterministic frontend ScenarioCalculator synchronously.
 * Round 2: swap computeScenario() with api.computeScenario() — zero component changes.
 *
 * No artificial loading delay. Loading state reflects real async work only.
 */
import { useState, useCallback, useEffect } from 'react';
import type { ScenarioInput, ScenarioResult } from '../types/scenario';
import type { AirQualityReading } from '../types/airQuality';
import { computeScenario } from '../lib/scenarioCalculator';

interface ScenarioState {
  result: ScenarioResult | null;
  loading: boolean;
  error: string | null;
  run: (input: ScenarioInput, baseline: AirQualityReading) => void;
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

  const run = useCallback((input: ScenarioInput, baseline: AirQualityReading) => {
    globalLoading = true;
    globalError = null;
    notify();
    try {
      // Synchronous deterministic calculation — no fake delay
      globalResult = computeScenario(input, baseline);
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
