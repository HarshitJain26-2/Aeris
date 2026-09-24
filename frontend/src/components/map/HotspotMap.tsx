import React, { useRef, useEffect, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { HotspotGeoJSON, HotspotFeature } from '../../types/hotspot';

interface HotspotMapProps {
  geoJson: HotspotGeoJSON | null;
  mode: 'observed' | 'modelled';
  onZoneSelect: (feature: HotspotFeature | null) => void;
}

export const HotspotMap: React.FC<HotspotMapProps> = ({ geoJson, mode, onZoneSelect }) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm': {
            type: 'raster',
            tiles: [
              'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap Contributors'
          }
        },
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: {
              'background-color': '#1a1917'
            }
          },
          {
            id: 'osm-layer',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19,
            paint: {
              'raster-saturation': -1,
              'raster-brightness-max': 0.3,
              'raster-contrast': 0.2
            }
          }
        ]
      },
      center: [73.8567, 18.5204], // Pune
      zoom: 11,
      pitch: 40,
      attributionControl: false,
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'bottom-right');
    map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

    map.current.on('load', () => {
      setMapLoaded(true);
      // Force a resize once style loads, just in case
      map.current?.resize();
    });

    const resizeObserver = new ResizeObserver(() => {
      map.current?.resize();
    });
    resizeObserver.observe(mapContainer.current);

    return () => {
      resizeObserver.disconnect();
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapLoaded || !map.current || !geoJson) return;

    const sourceId = 'hotspots-source';
    
    if (map.current.getSource(sourceId)) {
      (map.current.getSource(sourceId) as maplibregl.GeoJSONSource).setData(geoJson);
    } else {
      map.current.addSource(sourceId, {
        type: 'geojson',
        data: geoJson,
      });

      // Heatmap layer
      map.current.addLayer({
        id: 'hotspots-heatmap',
        type: 'heatmap',
        source: sourceId,
        paint: {
          'heatmap-weight': ['get', 'intensity'],
          'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 11, 1, 15, 3],
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0, 'rgba(0,0,0,0)',
            0.2, 'rgba(132, 204, 22, 0.6)', // Satisfactory
            0.4, 'rgba(234, 179, 8, 0.7)',  // Moderate
            0.6, 'rgba(249, 115, 22, 0.8)', // Poor
            0.8, 'rgba(239, 68, 68, 0.9)',  // Very Poor
            1, 'rgba(153, 27, 27, 1)'       // Severe
          ],
          'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 11, 20, 15, 50],
          'heatmap-opacity': 0.8,
        },
      });

      // Interactive points layer
      map.current.addLayer({
        id: 'hotspots-points',
        type: 'circle',
        source: sourceId,
        paint: {
          'circle-radius': 7,
          'circle-color': [
            'interpolate',
            ['linear'],
            ['get', 'intensity'],
            0.2, '#84cc16', // Satisfactory
            0.5, '#eab308', // Moderate
            0.8, '#f97316', // Poor
            1, '#ef4444' // Severe/Very Poor
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#1a1917',
        },
      });

      map.current.on('mouseenter', 'hotspots-points', () => {
        if (map.current) map.current.getCanvas().style.cursor = 'pointer';
      });
      map.current.on('mouseleave', 'hotspots-points', () => {
        if (map.current) map.current.getCanvas().style.cursor = '';
      });

      map.current.on('click', 'hotspots-points', (e: maplibregl.MapLayerMouseEvent) => {
        if (e.features && e.features[0]) {
          // Cast feature correctly
          const feature = e.features[0] as unknown as HotspotFeature;
          // Parse properties since MapLibre returns them as strings sometimes if nested
          if (typeof feature.properties === 'string') {
            feature.properties = JSON.parse(feature.properties);
          }
          onZoneSelect(feature);
        }
      });
      
      map.current.on('click', (e: maplibregl.MapMouseEvent) => {
        const features = map.current?.queryRenderedFeatures(e.point, { layers: ['hotspots-points'] });
        if (!features || features.length === 0) {
          onZoneSelect(null);
        }
      });
    }

    // Update heatmap opacity based on mode
    if (map.current.getLayer('hotspots-heatmap')) {
      const opacity = mode === 'observed' ? 0.8 : 0.55;
      map.current.setPaintProperty('hotspots-heatmap', 'heatmap-opacity', opacity);
    }
    
  }, [mapLoaded, geoJson, mode, onZoneSelect]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, background: 'var(--color-bg-base)' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
