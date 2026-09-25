import type { CpcbBand } from './airQuality';

export interface UrbanZone {
  zone_id: string;
  name: string;
  latitude: number;
  longitude: number;
  description: string;
  cameras: string[];
  cameraCount: number;
  areaType: string;
  nearestStation?: string;
  distanceToStationKm?: number;
}

export type SelectedMapEntity =
  | {
      type: 'zone';
      zone: UrbanZone;
      airshedPm25?: number | null;
      airshedAqi?: number | null;
      airshedBand?: CpcbBand | null;
      timestamp?: string | null;
      dataSource: 'observed' | 'model_estimate' | 'DEMO_FIXTURE';
    }
  | {
      type: 'hotspot';
      id: string;
      name: string;
      locality: string;
      latitude: number;
      longitude: number;
      pm25: number;
      aqi: number;
      aqiBand: CpcbBand;
      dominantDriver: 'Traffic' | 'Industrial' | 'Residential/Biomass';
      intensity: number;
      timestamp?: string | null;
      dataSource: 'observed' | 'model_estimate' | 'DEMO_FIXTURE';
    };
