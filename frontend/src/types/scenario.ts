import type { CpcbBand } from './airQuality';

/**
 * Input contract for the scenario calculator.
 * This interface is identical for the frontend calculator
 * and the future backend POST /api/v1/scenario endpoint.
 */
export interface ScenarioInput {
  /** Percentage reduction in traffic volume: 0 – 50 */
  trafficReductionPct: number;
}

export interface AirQualitySnapshot {
  pm25: number;
  aqi: number;
  aqiBand: CpcbBand;
}

/**
 * Result contract — same shape for frontend calculator and backend solver.
 * When method === 'frontend-linear-v1', this is a deterministic approximation.
 * When method === 'backend-solver', this comes from the ML model.
 */
export interface ScenarioResult {
  input: ScenarioInput;
  baseline: AirQualitySnapshot;
  modelled: AirQualitySnapshot;
  /** Absolute PM2.5 reduction in µg/m³ */
  deltaAbsolute: number;
  /** Percentage PM2.5 reduction (positive = improvement) */
  deltaPct: number;
  /**
   * 'frontend-linear-v1' = deterministic frontend approximation
   * 'backend-solver'     = future ML-backed result
   */
  method: 'frontend-linear-v1' | 'backend-solver';
  /** Displayed to user — always present */
  disclaimer: string;
  /** Always true for model-estimated outputs */
  isModelEstimate: true;
}
