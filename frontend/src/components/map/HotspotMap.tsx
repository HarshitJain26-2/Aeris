import React, { useRef, useEffect, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { HotspotGeoJSON, HotspotFeature } from '../../types/hotspot';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { Skeleton } from '../ui/Skeleton';
import { useScenario } from '../../hooks/useScenario';

interface HotspotMapProps {
  geoJson: HotspotGeoJSON | null;
  mode: 'observed' | 'modelled';
  loading?: boolean;
  onZoneSelect: (feature: HotspotFeature | null) => void;
}

export const HotspotMap: React.FC<HotspotMapProps> = ({ geoJson, mode, loading, onZoneSelect }) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState(false);
  const { result: scenarioResult } = useScenario();

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
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

    map.current.on('error', (e) => {
      if (e && e.error) {
        setMapError(true);
      }
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
    
    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

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
            0.2, 'rgba(74, 222, 128, 0.6)',  // Good
            0.4, 'rgba(250, 204, 21, 0.7)',  // Moderate
            0.6, 'rgba(251, 146, 60, 0.8)',  // Poor
            0.8, 'rgba(239, 68, 68, 0.9)',   // Severe
            1, 'rgba(153, 27, 27, 1)'        // Hazardous
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
          'circle-color-transition': { duration: 800, delay: 0 } as any,
          'circle-radius-transition': { duration: 800, delay: 0 } as any,
          'circle-radius': [
            'step',
            ['get', 'aqi'],
            6,      // Good
            50, 8,  // Moderate
            100, 10, // Poor
            200, 12, // Severe
            300, 14  // Hazardous
          ],
          'circle-color': [
            'step',
            ['get', 'aqi'],
            '#4ADE80', // Good (<= 50)
            50, '#FACC15', // Moderate (> 50 and <= 100)
            100, '#FB923C', // Poor (> 100 and <= 200)
            200, '#EF4444', // Severe (> 200 and <= 300)
            300, '#991B1B'  // Hazardous (> 300)
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#1a1917',
        } as any,
      });

      map.current.on('mouseenter', 'hotspots-points', (e) => {
        if (!map.current || !e.features || !e.features[0]) return;
        map.current.getCanvas().style.cursor = 'pointer';
        
        const feature = e.features[0];
        const coordinates = (feature.geometry as any).coordinates.slice();
        const props = typeof feature.properties === 'string' ? JSON.parse(feature.properties as any) : feature.properties;
        const isModelled = props.dataSource === 'model_estimate';
        const statusColor = isModelled ? 'var(--color-modelled)' : 'var(--color-observed)';
        const statusText = isModelled ? 'Model Estimate' : 'Observed';

        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
          coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        const html = `
          <div style="padding: 8px 12px; font-family: var(--font-sans); font-size: 12px; color: var(--color-text-primary);">
            <div style="font-weight: 600; margin-bottom: 4px;">${props.name}</div>
            <div style="color: var(--color-text-secondary); margin-bottom: 2px;">AQI: <span style="color: var(--color-text-primary); font-weight: 500;">${props.aqi}</span></div>
            <div style="color: var(--color-text-secondary); margin-bottom: 4px;">PM2.5: <span style="color: var(--color-text-primary); font-weight: 500;">${props.pm25}</span> <span style="color: var(--color-text-muted);">µg/m³</span></div>
            <div style="color: ${statusColor}; margin-top: 4px;">${statusText}</div>
          </div>
        `;

        popup.setLngLat(coordinates).setHTML(html).addTo(map.current);
      });
      map.current.on('mouseleave', 'hotspots-points', () => {
        if (map.current) map.current.getCanvas().style.cursor = '';
        popup.remove();
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

  useEffect(() => {
    if (!map.current || !mapLoaded || !map.current.getLayer('hotspots-points')) return;

    const reductionFactor = scenarioResult ? Math.max(0, 1 - (scenarioResult.deltaPct / 100)) : 1;
    const effectiveAqi = ['*', ['get', 'aqi'], reductionFactor];

    map.current.setPaintProperty('hotspots-points', 'circle-color', [
      'step',
      effectiveAqi,
      '#4ADE80',
      50, '#FACC15',
      100, '#FB923C',
      200, '#EF4444',
      300, '#991B1B'
    ]);
    
    map.current.setPaintProperty('hotspots-points', 'circle-radius', [
      'step',
      effectiveAqi,
      6,
      50, 8,
      100, 10,
      200, 12,
      300, 14
    ]);
  }, [scenarioResult, mapLoaded]);

  // Fallback timeout to ensure mapLoaded doesn't get stuck if MapLibre fails to emit 'load' silently
  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    if (map.current && !mapLoaded) {
      timeout = setTimeout(() => setMapLoaded(true), 2000);
    }
    return () => clearTimeout(timeout);
  }, [map.current, mapLoaded]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, background: 'var(--color-bg-base)' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      {loading && (
        <div className="absolute inset-0 z-[70] bg-bg-base pointer-events-none">
          <Skeleton width="100%" height="100%" borderRadius="var(--radius-xl)" />
        </div>
      )}
      {mapError && !loading && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-bg-base/90 p-4">
          <ErrorState title="Map failed to load" onRetry={() => window.location.reload()} />
        </div>
      )}
      {(!geoJson || !geoJson.features || geoJson.features.length === 0) && !mapError && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-bg-base/80 backdrop-blur-sm p-4">
          <EmptyState title="No hotspots detected in this time window" hint="There is no zone data available for this time period." />
        </div>
      )}
      {/* Keyboard accessible zone list */}
      {geoJson && geoJson.features && geoJson.features.length > 0 && (
        <ul className="sr-only focus-within:not-sr-only focus-within:absolute focus-within:top-4 focus-within:left-4 focus-within:z-[60] focus-within:bg-bg-elevated focus-within:p-2 focus-within:shadow-card focus-within:rounded-lg focus-within:max-h-[300px] focus-within:overflow-y-auto focus-within:border focus-within:border-border">
          <li className="text-xs font-semibold text-text-secondary px-2 mb-2 uppercase">Keyboard Map Navigation</li>
          {geoJson.features.map((feature, i) => (
            <li key={feature.properties.id || i}>
              <button
                onClick={() => onZoneSelect(feature)}
                className="w-full text-left px-2 py-1.5 text-sm text-text-primary rounded hover:bg-bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              >
                {feature.properties.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
