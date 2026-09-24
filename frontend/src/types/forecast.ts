/**
 * AERIS Urban Environmental Intelligence & Digital Twin
 * Forecast Type Definitions
 * 
 * Strict interfaces for observed PM2.5 and 24-hour temporal projections.
 * Distinguishes between OBSERVED (real measurements) and MODELED (ML predictions).
 */

export interface ForecastPoint {
  /** ISO-8601 timestamp string or hourly time label (e.g. "2026-09-24T10:00:00Z" or "10:00") */
  timestamp: string;
  /** Actual observed PM2.5 concentration in µg/m³. Null or undefined for future forecast hours */
  actual?: number | null;
  /** Modeled/predicted PM2.5 concentration in µg/m³ */
  predicted: number;
}

export interface ZoneForecast {
  /** Unique zone identifier (e.g. "zone-01") */
  zoneId: string;
  /** Human-readable zone name (e.g. "Zone 01 - Shivajinagar") */
  zoneName: string;
  /** Current observed PM2.5 value, or null if no observation sensor data is available */
  currentPm25: number | null;
  /** 24-hour temporal forecast sequence of actual vs predicted points */
  forecast: ForecastPoint[];
  /** Timestamp when the forecast model was run or data was last updated */
  lastUpdated?: string;
  /** Measurement unit (standard: "µg/m³") */
  unit?: string;
}

export type ForecastStatus = 'idle' | 'loading' | 'success' | 'empty' | 'error';
