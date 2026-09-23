/**
 * AERIS API Service Layer
 *
 * Single entry point for all data fetching.
 * VITE_USE_MOCK=true (default) → resolves mock fixtures from src/mocks/
 * VITE_USE_MOCK=false          → fetches from VITE_API_BASE_URL
 *
 * Zero component code changes needed to switch between mock and real API.
 */

import type { AirQualityReading } from '../types/airQuality';
import type { ForecastResponse } from '../types/forecast';
import type { HotspotGeoJSON } from '../types/hotspot';
import type { DriverAttributionResponse } from '../types/source';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

// ── Air Quality ──────────────────────────────────────────────

export async function getCurrentAirQuality(): Promise<AirQualityReading> {
  if (USE_MOCK) {
    const mod = await import('../mocks/airQualityObserved.json');
    return mod.default as unknown as AirQualityReading;
  }
  return fetchJson<AirQualityReading>('/api/v1/current');
}

// ── Forecast ─────────────────────────────────────────────────

export async function getForecast(): Promise<ForecastResponse> {
  if (USE_MOCK) {
    const mod = await import('../mocks/pm25Forecast.json');
    return mod.default as unknown as ForecastResponse;
  }
  return fetchJson<ForecastResponse>('/api/v1/forecast');
}

// ── Hotspots ─────────────────────────────────────────────────

export async function getHotspots(): Promise<HotspotGeoJSON> {
  if (USE_MOCK) {
    const mod = await import('../mocks/hotspots.json');
    return mod.default as unknown as HotspotGeoJSON;
  }
  return fetchJson<HotspotGeoJSON>('/api/v1/hotspots');
}

// ── Driver Attribution ────────────────────────────────────────

export async function getDriverAttribution(): Promise<DriverAttributionResponse> {
  if (USE_MOCK) {
    const mod = await import('../mocks/sourceAttribution.json');
    return mod.default as unknown as DriverAttributionResponse;
  }
  return fetchJson<DriverAttributionResponse>('/api/v1/drivers');
}
