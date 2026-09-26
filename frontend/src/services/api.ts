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
import type { UrbanZone } from '../types/zone';
import type { ScenarioResult } from '../types/scenario';
import { DOCUMENTED_ZONES_LIST, ZONE_LOOKUP } from '../data/puneZones';
import { computeScenario } from '../lib/scenarioCalculator';

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

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
  try {
    return await fetchJson<HotspotGeoJSON>('/api/v1/hotspots');
  } catch (err) {
    console.warn('Real /api/v1/hotspots unavailable; retaining DEMO_FIXTURE provenance', err);
    const mod = await import('../mocks/hotspots.json');
    return mod.default as unknown as HotspotGeoJSON;
  }
}

// ── Driver Attribution ────────────────────────────────────────

export async function getDriverAttribution(): Promise<DriverAttributionResponse> {
  if (USE_MOCK) {
    const mod = await import('../mocks/sourceAttribution.json');
    return mod.default as unknown as DriverAttributionResponse;
  }
  try {
    return await fetchJson<DriverAttributionResponse>('/api/v1/drivers');
  } catch (err) {
    console.warn('Real /api/v1/drivers unavailable; retaining DEMO_FIXTURE provenance', err);
    const mod = await import('../mocks/sourceAttribution.json');
    return mod.default as unknown as DriverAttributionResponse;
  }
}

// ── Monitored Zones ──────────────────────────────────────────

export async function getZones(): Promise<UrbanZone[]> {
  if (USE_MOCK) {
    return Promise.resolve(DOCUMENTED_ZONES_LIST);
  }
  try {
    const rawZones = await fetchJson<Array<Partial<UrbanZone> & { zone_id: string }>>('/api/v1/zones');
    return rawZones.map((z) => {
      const enriched = ZONE_LOOKUP[z.zone_id] || {};
      return {
        ...enriched,
        ...z,
        cameras: z.cameras || enriched.cameras || [],
        cameraCount: z.cameraCount ?? enriched.cameraCount ?? (enriched.cameras?.length ?? 0),
        areaType: z.areaType || enriched.areaType || 'Monitored Urban Corridor',
        description: z.description || enriched.description || '',
      } as UrbanZone;
    });
  } catch (err) {
    console.warn('Real /api/v1/zones failed; falling back to documented zones', err);
    return Promise.resolve(DOCUMENTED_ZONES_LIST);
  }
}

// ── Scenario Simulation ──────────────────────────────────────

export async function simulateScenario(
  trafficReductionPct: number,
  baseline?: AirQualityReading
): Promise<ScenarioResult> {
  if (USE_MOCK) {
    if (baseline) {
      return computeScenario({ trafficReductionPct }, baseline);
    }
    const current = await getCurrentAirQuality();
    return computeScenario({ trafficReductionPct }, current);
  }

  const res = await fetch(`${API_BASE}/api/scenario/simulate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ traffic_reduction_pct: trafficReductionPct }),
  });

  if (!res.ok) {
    let detailMsg = `Scenario API error ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson.detail) detailMsg = errorJson.detail;
    } catch {
      // ignore
    }
    throw new Error(detailMsg);
  }

  const data = await res.json();

  return {
    input: data.input || { trafficReductionPct },
    baseline: data.baseline || {
      pm25: data.baseline_pm25,
      aqi: Math.round(data.baseline_pm25 * 2.2),
      aqiBand: 'Moderate',
    },
    modelled: data.modelled || {
      pm25: data.scenario_pm25,
      aqi: Math.round(data.scenario_pm25 * 2.2),
      aqiBand: 'Moderate',
    },
    deltaAbsolute: data.deltaAbsolute ?? Math.abs(data.delta),
    deltaPct: data.deltaPct ?? Math.abs(data.percent_change),
    method: 'backend-solver',
    disclaimer: data.disclaimer || 'Model-estimated scenario change under the specified traffic reduction.',
    isModelEstimate: true,
  };
}
