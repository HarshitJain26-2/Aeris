import type { CpcbBand } from './airQuality';

export interface ForecastPoint {
  /** ISO 8601 timestamp */
  timestamp: string;
  /** PM2.5 in µg/m³ */
  pm25: number;
  /** CPCB AQI */
  aqi: number;
  /** CPCB band */
  aqiBand: CpcbBand;
  /** 'observed' = actual sensor reading; 'forecast' = model prediction */
  type: 'observed' | 'forecast';
  /** Lower bound of 90% CI (forecast only) */
  pm25Lower?: number;
  /** Upper bound of 90% CI (forecast only) */
  pm25Upper?: number;
  /** Data provenance */
  dataSource: 'observed' | 'model_estimate' | 'DEMO_FIXTURE';
}

export interface ForecastResponse {
  city: string;
  generatedAt: string;
  horizonHours: number;
  points: ForecastPoint[];
  modelVersion: string;
  dataSource: 'model_estimate' | 'DEMO_FIXTURE';
}
