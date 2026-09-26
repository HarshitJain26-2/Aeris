export type DriverCategory =
  | 'Recent PM2.5 history'
  | 'Weather'
  | 'Traffic'
  | 'Time / calendar';

/**
 * Normalized mean absolute SHAP feature-attribution shares.
 * These are model feature attributions, NOT physical emission-source
 * apportionment percentages, and must never be described as causal proof
 * that a source category causes a specific fraction of PM2.5.
 */
export interface DriverAttribution {
  category: DriverCategory;
  /** Estimated percentage contribution (normalized mean absolute SHAP feature attribution) */
  estimatedPct: number;
  /** Confidence interval lower bound (pct) */
  ciLower: number;
  /** Confidence interval upper bound (pct) */
  ciUpper: number;
  /** Human-readable description */
  description: string;
}

export interface DriverAttributionResponse {
  city: string;
  period: string;
  drivers: DriverAttribution[];
  /**
   * Attribution method:
   * - 'model_feature_attribution': normalized mean absolute SHAP feature-attribution shares.
   * - 'DEMO_FIXTURE': development fixture.
   */
  method: 'model_feature_attribution' | 'DEMO_FIXTURE';
  disclaimer: string;
  dataSource: 'model_estimate' | 'DEMO_FIXTURE';
}
