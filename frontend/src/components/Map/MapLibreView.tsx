import { useEffect, useRef } from 'react';
import { Map as MapLibreMap, NavigationControl, config, type StyleSpecification } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import { PUNE_MOCK_ZONES } from '../../data/puneZones';
import './MapLibreView.css';

// Configure MapLibre web worker for Vite
config.WORKER_URL = maplibreWorkerUrl;

// Pune geographical coordinates [longitude, latitude]
const PUNE_CENTER: [number, number] = [73.8567, 18.5204];
const DEFAULT_ZOOM = 11.2;

const BASEMAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    'osm-tiles': {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
  layers: [
    {
      id: 'osm-tiles-layer',
      type: 'raster',
      source: 'osm-tiles',
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

export const MapLibreView = () => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<MapLibreMap | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new MapLibreMap({
      container: mapContainerRef.current,
      style: BASEMAP_STYLE,
      center: PUNE_CENTER,
      zoom: DEFAULT_ZOOM,
    });

    mapInstanceRef.current = map;

    // Standard map navigation controls
    map.addControl(new NavigationControl(), 'top-right');

    map.on('load', () => {
      // Add Pune mock zones GeoJSON source
      if (!map.getSource('pune-zones')) {
        map.addSource('pune-zones', {
          type: 'geojson',
          data: PUNE_MOCK_ZONES,
        });
      }

      // Add polygon fill layer
      if (!map.getLayer('pune-zones-fill')) {
        map.addLayer({
          id: 'pune-zones-fill',
          type: 'fill',
          source: 'pune-zones',
          paint: {
            'fill-color': '#0284c7',
            'fill-opacity': 0.2,
          },
        });
      }

      // Add polygon outline layer
      if (!map.getLayer('pune-zones-outline')) {
        map.addLayer({
          id: 'pune-zones-outline',
          type: 'line',
          source: 'pune-zones',
          paint: {
            'line-color': '#0369a1',
            'line-width': 2,
          },
        });
      }

      // Add visible zone labels
      if (!map.getLayer('pune-zones-labels')) {
        map.addLayer({
          id: 'pune-zones-labels',
          type: 'symbol',
          source: 'pune-zones',
          layout: {
            'text-field': ['get', 'name'],
            'text-size': 12,
            'text-anchor': 'center',
            'text-allow-overlap': true,
          },
          paint: {
            'text-color': '#0f172a',
            'text-halo-color': '#ffffff',
            'text-halo-width': 1.5,
          },
        });
      }
    });

    // Handle container resizing smoothly
    const resizeObserver = new ResizeObserver(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.resize();
      }
    });

    if (mapContainerRef.current) {
      resizeObserver.observe(mapContainerRef.current);
    }

    const handleWindowResize = () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.resize();
      }
    };

    window.addEventListener('resize', handleWindowResize);

    return () => {
      window.removeEventListener('resize', handleWindowResize);
      resizeObserver.disconnect();
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  return (
    <div className="map-container-wrapper">
      <div className="map-overlay-info">
        <div className="map-overlay-title">Pune Urban Environmental Twin</div>
        <div className="map-overlay-subtitle">
          <span className="status-dot"></span>
          GIS Layer Active: 6 Urban Zones Loaded
        </div>
      </div>

      <div ref={mapContainerRef} className="map-container" />

      <div className="map-legend">
        <div className="map-legend-title">Active Test Zones</div>
        <div className="map-legend-list">
          {PUNE_MOCK_ZONES.features.map((feature) => (
            <div key={feature.properties.id} className="map-legend-item">
              <span className="legend-swatch"></span>
              <span>{feature.properties.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
