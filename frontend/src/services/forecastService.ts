/**
 * AERIS Urban Environmental Intelligence & Digital Twin
 * Forecast Service Layer
 * 
 * Provides communication interface to the backend forecast endpoints.
 * Calls: GET /api/forecast?zone_id=<zoneId>
 * Handles network failures gracefully without hardcoding fake production data.
 */

import type { ZoneForecast, ForecastPoint } from '../types/forecast';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

interface RawForecastPoint {
  timestamp: string;
  actual?: number | null;
  predicted?: number;
  modeled?: number;
}

interface RawZoneForecastResponse {
  zone_id?: string;
  zoneId?: string;
  zone_name?: string;
  zoneName?: string;
  current_pm25?: number | null;
  currentPm25?: number | null;
  forecast?: RawForecastPoint[];
  last_updated?: string;
  lastUpdated?: string;
  unit?: string;
}

/**
 * Fetches the 24-hour PM2.5 forecast for a specified urban zone.
 * 
 * @param zoneId Unique identifier of the zone (e.g. "zone-01")
 * @param signal Optional AbortSignal for canceling in-flight requests
 * @returns Promise resolving to normalized ZoneForecast
 * @throws Error if the backend service is unreachable or returns a non-OK status
 */
export async function getZoneForecast(
  zoneId: string,
  signal?: AbortSignal
): Promise<ZoneForecast> {
  const endpoint = `${API_BASE_URL}/api/forecast?zone_id=${encodeURIComponent(zoneId)}`;

  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    signal,
  });

  if (!response.ok) {
    throw new Error(`Forecast service returned HTTP ${response.status}: ${response.statusText}`);
  }

  const data: RawZoneForecastResponse = await response.json();

  const forecastPoints: ForecastPoint[] = (data.forecast || []).map((point) => ({
    timestamp: point.timestamp,
    actual: point.actual ?? null,
    predicted: point.predicted ?? point.modeled ?? 0,
  }));

  return {
    zoneId: data.zoneId || data.zone_id || zoneId,
    zoneName: data.zoneName || data.zone_name || zoneId,
    currentPm25: data.currentPm25 ?? data.current_pm25 ?? null,
    forecast: forecastPoints,
    lastUpdated: data.lastUpdated || data.last_updated,
    unit: data.unit || 'µg/m³',
  };
}
