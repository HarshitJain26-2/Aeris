/**
 * AERIS Deterministic Frontend Scenario Calculator
 *
 * This module provides a synchronous, deterministic linear model for the
 * "what-if" scenario panel. It uses the same ScenarioInput / ScenarioResult
 * TypeScript contract that the future backend POST /api/v1/scenario will implement.
 *
 * When the backend is ready, useScenario.ts will switch from calling this
 * function to calling api.computeScenario() — zero component changes needed.
 *
 * Model basis:
 *  - Urban India traffic contributes ~40% of ambient PM2.5
 *    (CPCB Source Apportionment Studies, 2022 synthesis)
 *  - Elasticity coefficient 0.80 (conservative linear estimate)
 *  - Formula: PM2.5_modelled = PM2.5_baseline × (1 − reduction × 0.40 × 0.80)
 *
 * Limitations (displayed to user):
 *  - Linear model; ignores meteorological feedback, secondary aerosol formation
 *  - Does not account for temporal variation or spatial heterogeneity
 *  - Replace with backend ML solver for production use
 */

import type { ScenarioInput, ScenarioResult } from '../types/scenario';
import type { AirQualityReading } from '../types/airQuality';
import { getBandFromPm25, estimateAqiFromPm25 } from './cpcbAqi';

/**
 * Traffic share of urban PM2.5 contribution (CPCB 2022 synthesis).
 * This is a population-weighted average for Indian metro areas.
 */
const TRAFFIC_SHARE = 0.40;

/**
 * Elasticity coefficient (conservative): each 1% traffic volume reduction
 * produces ELASTICITY × TRAFFIC_SHARE × 1% PM2.5 reduction.
 * Set to 0.80 (i.e., sub-linear, accounting for non-traffic background).
 */
const ELASTICITY = 0.80;

const DISCLAIMER =
  'Frontend linear model estimate (v1). ' +
  'Formula: PM₂.₅_modelled = baseline × (1 − reduction × 0.40 × 0.80). ' +
  'Assumes traffic ~40% PM2.5 share (CPCB 2022). ' +
  'Replace with backend solver for validated results.';

export function computeScenario(
  input: ScenarioInput,
  baseline: AirQualityReading,
): ScenarioResult {
  const { trafficReductionPct } = input;

  // Clamp input to valid range
  const clampedReduction = Math.min(50, Math.max(0, trafficReductionPct));

  // Core linear formula — deterministic, no randomness
  const reductionFactor = 1 - (clampedReduction / 100) * TRAFFIC_SHARE * ELASTICITY;
  const modelledPm25 = Math.round(baseline.pm25 * reductionFactor * 10) / 10;

  const deltaAbsolute = Math.round((baseline.pm25 - modelledPm25) * 10) / 10;
  const deltaPct = Math.round(((baseline.pm25 - modelledPm25) / baseline.pm25) * 100 * 10) / 10;

  const modelledAqi = estimateAqiFromPm25(modelledPm25);
  const modelledBand = getBandFromPm25(modelledPm25);
  const baselineBand = getBandFromPm25(baseline.pm25);

  return {
    input: { trafficReductionPct: clampedReduction },
    baseline: {
      pm25: baseline.pm25,
      aqi: baseline.aqi,
      aqiBand: baselineBand.band,
    },
    modelled: {
      pm25: modelledPm25,
      aqi: modelledAqi,
      aqiBand: modelledBand.band,
    },
    deltaAbsolute,
    deltaPct,
    method: 'frontend-linear-v1',
    disclaimer: DISCLAIMER,
    isModelEstimate: true,
  };
}
