import type { CpcbBand } from './airQuality';

export interface HotspotProperties {
  id: string;
  name: string;
  /** Locality / neighbourhood name */
  locality: string;
  pm25: number;
  aqi: number;
  aqiBand: CpcbBand;
  /** Dominant driver category */
  dominantDriver: 'Traffic' | 'Industrial' | 'Residential/Biomass';
  /** Heatmap intensity weight 0–1 */
  intensity: number;
  dataSource: 'observed' | 'model_estimate' | 'DEMO_FIXTURE';
}

export interface HotspotFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [longitude: number, latitude: number];
  };
  properties: HotspotProperties;
}

export interface HotspotGeoJSON {
  type: 'FeatureCollection';
  features: HotspotFeature[];
  metadata: {
    city: string;
    generatedAt: string;
    dataSource: 'observed' | 'model_estimate' | 'DEMO_FIXTURE';
  };
}
