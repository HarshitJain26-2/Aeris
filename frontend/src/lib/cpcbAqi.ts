/**
 * India National AQI (CPCB) calculation utilities.
 *
 * Reference: Central Pollution Control Board, AQI Calculation Manual (2014)
 * https://cpcb.nic.in/displaypdf.php?id=bmF0aW9uYWwtYWlyLXF1YWxpdHktaW5kZXgvcmVwb3J0LnBkZg==
 *
 * NOTE: These are CPCB/National AQI thresholds, NOT WHO guideline values.
 * WHO 24h PM2.5 guideline = 15 µg/m³ (2021), which is far stricter than CPCB Good band.
 */

import type { CpcbBand } from '../types/airQuality';

export interface AqiBandInfo {
  band: CpcbBand;
  label: string;
  aqiMin: number;
  aqiMax: number;
  pm25Min: number;
  pm25Max: number;
  /** CSS hex colour for this band */
  color: string;
  /** CSS variable reference */
  cssVar: string;
  /** Brief health guidance */
  healthGuidance: string;
}

export const CPCB_BANDS: AqiBandInfo[] = [
  {
    band: 'Good',
    label: 'Good',
    aqiMin: 0, aqiMax: 50,
    pm25Min: 0, pm25Max: 30,
    color: '#22c55e',
    cssVar: 'var(--aqi-good)',
    healthGuidance: 'Air quality is satisfactory.',
  },
  {
    band: 'Satisfactory',
    label: 'Satisfactory',
    aqiMin: 51, aqiMax: 100,
    pm25Min: 31, pm25Max: 60,
    color: '#84cc16',
    cssVar: 'var(--aqi-satisfactory)',
    healthGuidance: 'May cause minor discomfort for sensitive individuals.',
  },
  {
    band: 'Moderate',
    label: 'Moderate',
    aqiMin: 101, aqiMax: 200,
    pm25Min: 61, pm25Max: 90,
    color: '#eab308',
    cssVar: 'var(--aqi-moderate)',
    healthGuidance: 'Breathing discomfort for people with asthma and heart disease.',
  },
  {
    band: 'Poor',
    label: 'Poor',
    aqiMin: 201, aqiMax: 300,
    pm25Min: 91, pm25Max: 120,
    color: '#f97316',
    cssVar: 'var(--aqi-poor)',
    healthGuidance: 'Breathing discomfort for most people. Avoid prolonged outdoor exposure.',
  },
  {
    band: 'Very Poor',
    label: 'Very Poor',
    aqiMin: 301, aqiMax: 400,
    pm25Min: 121, pm25Max: 250,
    color: '#ef4444',
    cssVar: 'var(--aqi-very-poor)',
    healthGuidance: 'Respiratory illness possible on prolonged exposure. Avoid outdoor activity.',
  },
  {
    band: 'Severe',
    label: 'Severe',
    aqiMin: 401, aqiMax: 500,
    pm25Min: 251, pm25Max: 999,
    color: '#991b1b',
    cssVar: 'var(--aqi-severe)',
    healthGuidance: 'Serious health effects. Stay indoors. Use air purifier if possible.',
  },
];

/** Get band info from CPCB AQI value */
export function getBandFromAqi(aqi: number): AqiBandInfo {
  return (
    CPCB_BANDS.find((b) => aqi >= b.aqiMin && aqi <= b.aqiMax) ??
    CPCB_BANDS[CPCB_BANDS.length - 1]
  );
}

/** Get band info from PM2.5 concentration (µg/m³, 24h average) */
export function getBandFromPm25(pm25: number): AqiBandInfo {
  return (
    CPCB_BANDS.find((b) => pm25 >= b.pm25Min && pm25 <= b.pm25Max) ??
    CPCB_BANDS[CPCB_BANDS.length - 1]
  );
}

/**
 * Approximate AQI from PM2.5 using CPCB linear sub-index formula.
 * For display purposes — exact calculation requires all pollutants.
 */
export function estimateAqiFromPm25(pm25: number): number {
  const band = getBandFromPm25(pm25);
  if (!band) return 500;
  const { pm25Min, pm25Max, aqiMin, aqiMax } = band;
  const aqi =
    ((aqiMax - aqiMin) / (pm25Max - pm25Min)) * (pm25 - pm25Min) + aqiMin;
  return Math.round(Math.min(500, Math.max(0, aqi)));
}
