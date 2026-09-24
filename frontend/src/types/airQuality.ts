/** India CPCB AQI 6-band classification */
export type CpcbBand =
  | 'Good'
  | 'Satisfactory'
  | 'Moderate'
  | 'Poor'
  | 'Very Poor'
  | 'Severe';

export interface AirQualityReading {
  /** ISO 8601 timestamp of the reading */
  timestamp: string;
  /** City / location name */
  city: string;
  /** Station or area name */
  station: string;
  /** PM2.5 concentration in µg/m³ (24h average) */
  pm25: number;
  /** PM10 concentration in µg/m³ */
  pm10: number;
  /** India National AQI (CPCB) */
  aqi: number;
  /** CPCB AQI band */
  aqiBand: CpcbBand;
  /** Temperature in °C */
  temperatureC: number;
  /** Relative humidity % */
  humidityPct: number;
  /** Normalised traffic congestion index 0–100 */
  trafficIndex: number;
  /** Wind speed km/h */
  windSpeedKmh: number;
  /** Data provenance — must be 'observed' for sensor readings */
  dataSource: 'observed' | 'model_estimate' | 'DEMO_FIXTURE';
}
