/**
 * useScenario hook
 *
 * Round 1: calls the deterministic frontend ScenarioCalculator synchronously.
 * Round 2: swap computeScenario() with api.computeScenario() — zero component changes.
 *
 * No artificial loading delay. Loading state reflects real async work only.
 */
import { useState, useCallback } from 'react';
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

export function useScenario(): ScenarioState {
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback((input: ScenarioInput, baseline: AirQualityReading) => {
    setLoading(true);
    setError(null);
    try {
      // Synchronous deterministic calculation — no fake delay
      const r = computeScenario(input, baseline);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, run, reset };
}
