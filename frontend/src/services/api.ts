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
import type { ScenarioResult } from '../types/scenario';
import type { DriverAttributionResponse } from '../types/source';
import type { UrbanZone } from '../types/zone';
import { DOCUMENTED_ZONES_LIST } from '../data/puneZones';

export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';
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

// ── Monitored Zones ──────────────────────────────────────────

export async function getZones(): Promise<UrbanZone[]> {
  if (USE_MOCK) {
    return Promise.resolve(DOCUMENTED_ZONES_LIST);
  }
  return fetchJson<UrbanZone[]>('/api/v1/zones');
}

import type { ModelValidationEvidence } from '../types/validation';

// ── Scenario Simulation ──────────────────────────────────────

export async function simulateScenario(
  input: number | { trafficReductionPct: number },
  _baseline?: AirQualityReading
): Promise<ScenarioResult> {
  const pct = typeof input === 'number' ? input : input.trafficReductionPct;
  if (USE_MOCK) {
    const defaultBaseline: AirQualityReading = _baseline ?? {
      timestamp: new Date().toISOString(),
      city: 'Pune',
      station: 'Shivajinagar IITM SAFAR (Reference)',
      pm25: 68.0,
      pm10: 112.0,
      aqi: 127,
      aqiBand: 'Moderate',
      temperatureC: 22.4,
      humidityPct: 54,
      windSpeedKmh: 6.2,
      trafficIndex: 72,
      dataSource: 'DEMO_FIXTURE',
    };
    const { computeScenario } = await import('../lib/scenarioCalculator');
    return computeScenario({ trafficReductionPct: pct }, defaultBaseline);
  }
  const payload = { trafficReductionPct: pct, traffic_reduction_pct: pct };
  const res = await fetch(`${API_BASE}/api/scenario/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: /api/scenario/simulate`);
  return res.json() as Promise<ScenarioResult>;
}

// ── Model Validation Evidence ────────────────────────────────

export async function getModelValidation(): Promise<ModelValidationEvidence> {
  if (USE_MOCK) {
    return {
      model: 'XGBoost',
      target: 'pm25_target_t_plus_1',
      forecast_horizon: '1-hour-ahead (t+1h)',
      validation_type: 'temporal_holdout',
      target_source: 'CAMS Global Atmospheric Composition Forecasts',
      target_source_type: 'modeled',
      validation_rows: 23,
      training_rows: 144,
      feature_count: 25,
      mae: 5.6456,
      rmse: 7.9029,
      r2: 0.8885,
      persistence_mae: 7.2217,
      persistence_rmse: 11.1196,
      mae_improvement: 1.5761,
      rmse_improvement: 3.2167,
      mae_improvement_pct: 21.82,
      rmse_improvement_pct: 28.93,
      beats_persistence_mae: true,
      beats_persistence_rmse: true,
      disclaimer:
        'Ground-truth CPCB observations were unavailable across Pune CAAQMS stations during the Jan 11–18 2023 evaluation window due to a coordinated sensor offline period. Consequently, the modeling target is CAMS Global Atmospheric Composition Forecasts (modeled atmospheric PM2.5, source_type=modeled), not ground-station sensor measurements. The XGBoost model demonstrates genuine 1-hour-ahead predictive skill, beating the persistence baseline by 21.8% MAE and 28.9% RMSE on the unseen temporal holdout split.',
    };
  }
  return fetchJson<ModelValidationEvidence>('/api/v1/model/validation');
}
