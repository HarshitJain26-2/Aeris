import type { FeatureCollection, Polygon } from 'geojson';

export interface UrbanZoneProperties {
  id: string;
  name: string;
}

export const PUNE_MOCK_ZONES: FeatureCollection<Polygon, UrbanZoneProperties> = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      id: 1,
      properties: {
        id: 'zone-01',
        name: 'Zone 01',
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.835, 18.515],
            [73.865, 18.515],
            [73.865, 18.535],
            [73.835, 18.535],
            [73.835, 18.515],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      id: 2,
      properties: {
        id: 'zone-02',
        name: 'Zone 02',
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.790, 18.490],
            [73.820, 18.490],
            [73.820, 18.510],
            [73.790, 18.510],
            [73.790, 18.490],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      id: 3,
      properties: {
        id: 'zone-03',
        name: 'Zone 03',
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.910, 18.495],
            [73.940, 18.495],
            [73.940, 18.520],
            [73.910, 18.520],
            [73.910, 18.495],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      id: 4,
      properties: {
        id: 'zone-04',
        name: 'Zone 04',
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.900, 18.545],
            [73.935, 18.545],
            [73.935, 18.570],
            [73.900, 18.570],
            [73.900, 18.545],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      id: 5,
      properties: {
        id: 'zone-05',
        name: 'Zone 05',
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.795, 18.545],
            [73.825, 18.545],
            [73.825, 18.570],
            [73.795, 18.570],
            [73.795, 18.545],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      id: 6,
      properties: {
        id: 'zone-06',
        name: 'Zone 06',
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [73.840, 18.475],
            [73.875, 18.475],
            [73.875, 18.500],
            [73.840, 18.500],
            [73.840, 18.475],
          ],
        ],
      },
    },
  ],
};
