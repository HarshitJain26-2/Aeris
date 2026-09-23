export type DriverCategory = 'Traffic' | 'Industrial' | 'Residential/Biomass';

export interface DriverAttribution {
  category: DriverCategory;
  /** Estimated percentage contribution — approximate model estimate */
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
   * IMPORTANT: This must always be 'DEMO_FIXTURE' or 'model_estimate'.
   * Never claim causal proof from source apportionment.
   */
  method: 'DEMO_FIXTURE' | 'source_apportionment' | 'receptor_model';
  disclaimer: string;
  dataSource: 'model_estimate' | 'DEMO_FIXTURE';
}
