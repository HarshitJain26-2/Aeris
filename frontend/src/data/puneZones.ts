import type { FeatureCollection, Feature, Polygon } from 'geojson';
import type { UrbanZone } from '../types/zone';

export interface UrbanZoneProperties {
  id: string;
  zone_id: string;
  name: string;
  description: string;
  latitude: number;
  longitude: number;
  areaType: string;
  cameras: string[];
  cameraCount: number;
  nearestStation: string;
  distanceToStationKm: number;
}

export const DOCUMENTED_ZONES_LIST: UrbanZone[] = [
  {
    zone_id: 'PUNE_ALANKAR_CHOWK',
    name: 'Alankar Chowk',
    latitude: 18.5284,
    longitude: 73.8741,
    description: 'Alankar Chowk / Ambedkar Rd intersection',
    cameras: ['a2', 'a3'],
    cameraCount: 2,
    areaType: 'Commercial Junction & Traffic Corridor',
    nearestStation: 'Shivajinagar IITM SAFAR / MPCB Station',
    distanceToStationKm: 3.1,
  },
  {
    zone_id: 'PUNE_JEHANGIR_CHOWK',
    name: 'Jehangir Chowk',
    latitude: 18.5310,
    longitude: 73.8775,
    description: 'Jehangir Hospital / Sasoon Rd intersection',
    cameras: ['j1', 'j2', 'j3'],
    cameraCount: 3,
    areaType: 'Hospital Zone & Major Transit Arterial',
    nearestStation: 'Shivajinagar IITM SAFAR / MPCB Station',
    distanceToStationKm: 3.5,
  },
  {
    zone_id: 'PUNE_RTO_CHOWK',
    name: 'RTO Chowk',
    latitude: 18.5314,
    longitude: 73.8648,
    description: 'Regional Transport Office (RTO) Chowk / Sangam Bridge',
    cameras: ['r1', 'r2', 'r3'],
    cameraCount: 3,
    areaType: 'Transport Authority & River Crossing Corridor',
    nearestStation: 'Shivajinagar IITM SAFAR / MPCB Station',
    distanceToStationKm: 2.1,
  },
];

export const ZONE_LOOKUP: Record<string, UrbanZone> = DOCUMENTED_ZONES_LIST.reduce(
  (acc, zone) => {
    acc[zone.zone_id] = zone;
    return acc;
  },
  {} as Record<string, UrbanZone>
);

/**
 * GeoJSON FeatureCollection of the 3 documented ML junction zones in Pune.
 * Polygons represent the urban traffic corridor boundaries centered around each Chowk.
 */
export const PUNE_DOCUMENTED_ZONES: FeatureCollection<Polygon, UrbanZoneProperties> = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      id: 1,
      properties: {
        id: 'PUNE_ALANKAR_CHOWK',
        zone_id: 'PUNE_ALANKAR_CHOWK',
        name: 'Alankar Chowk',
        description: 'Alankar Chowk / Ambedkar Rd intersection',
        latitude: 18.5284,
        longitude: 73.8741,
        areaType: 'Commercial Junction & Traffic Corridor',
        cameras: ['a2', 'a3'],
        cameraCount: 2,
        nearestStation: 'Shivajinagar IITM SAFAR / MPCB Station',
        distanceToStationKm: 3.1,
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.8715, 18.5265],
            [73.8767, 18.5265],
            [73.8767, 18.5303],
            [73.8715, 18.5303],
            [73.8715, 18.5265],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      id: 2,
      properties: {
        id: 'PUNE_JEHANGIR_CHOWK',
        zone_id: 'PUNE_JEHANGIR_CHOWK',
        name: 'Jehangir Chowk',
        description: 'Jehangir Hospital / Sasoon Rd intersection',
        latitude: 18.5310,
        longitude: 73.8775,
        areaType: 'Hospital Zone & Major Transit Arterial',
        cameras: ['j1', 'j2', 'j3'],
        cameraCount: 3,
        nearestStation: 'Shivajinagar IITM SAFAR / MPCB Station',
        distanceToStationKm: 3.5,
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.8750, 18.5292],
            [73.8800, 18.5292],
            [73.8800, 18.5328],
            [73.8750, 18.5328],
            [73.8750, 18.5292],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      id: 3,
      properties: {
        id: 'PUNE_RTO_CHOWK',
        zone_id: 'PUNE_RTO_CHOWK',
        name: 'RTO Chowk',
        description: 'Regional Transport Office (RTO) Chowk / Sangam Bridge',
        latitude: 18.5314,
        longitude: 73.8648,
        areaType: 'Transport Authority & River Crossing Corridor',
        cameras: ['r1', 'r2', 'r3'],
        cameraCount: 3,
        nearestStation: 'Shivajinagar IITM SAFAR / MPCB Station',
        distanceToStationKm: 2.1,
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.8620, 18.5296],
            [73.8676, 18.5296],
            [73.8676, 18.5332],
            [73.8620, 18.5332],
            [73.8620, 18.5296],
          ],
        ],
      },
    },
  ],
};

// Backwards compatibility export
export const PUNE_MOCK_ZONES = PUNE_DOCUMENTED_ZONES;
export type { Feature };
