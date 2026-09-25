import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { HotspotGeoJSON, HotspotProperties } from '../../types/hotspot';
import type { SelectedMapEntity, UrbanZone } from '../../types/zone';
import { PUNE_DOCUMENTED_ZONES, DOCUMENTED_ZONES_LIST, ZONE_LOOKUP } from '../../data/puneZones';
import type { AirQualityReading } from '../../types/airQuality';
import type { ForecastResponse } from '../../types/forecast';

interface HotspotMapProps {
  geoJson: HotspotGeoJSON | null;
  mode: 'observed' | 'modelled';
  selectedEntity: SelectedMapEntity | null;
  onSelectEntity: (entity: SelectedMapEntity | null) => void;
  airQuality?: AirQualityReading | null;
  forecast?: ForecastResponse | null;
}

const PUNE_CENTER: [number, number] = [73.8700, 18.5250];
const DEFAULT_ZOOM = 12.8;

export const HotspotMap: React.FC<HotspotMapProps> = ({
  geoJson,
  mode,
  selectedEntity,
  onSelectEntity,
  airQuality,
  forecast,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const hoverPopupRef = useRef<maplibregl.Popup | null>(null);

  // Initialize MapLibre
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: PUNE_CENTER,
      zoom: DEFAULT_ZOOM,
      pitch: 30,
      attributionControl: false,
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
    map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
    });
    hoverPopupRef.current = popup;

    map.current.on('load', () => {
      setMapLoaded(true);
      map.current?.resize();
    });

    const resizeObserver = new ResizeObserver(() => {
      map.current?.resize();
    });
    resizeObserver.observe(mapContainer.current);

    return () => {
      resizeObserver.disconnect();
      popup.remove();
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Helper to construct zone entity
  const buildZoneEntity = useCallback(
    (zone: UrbanZone): SelectedMapEntity => {
      const isModelled = mode === 'modelled';
      const forecastTarget = forecast?.points?.find((p) => p.type === 'forecast');
      return {
        type: 'zone',
        zone,
        airshedPm25: isModelled ? (forecastTarget?.pm25 ?? 96.1) : (airQuality?.pm25 ?? 94.2),
        airshedAqi: isModelled ? (forecastTarget?.aqi ?? 215) : (airQuality?.aqi ?? 212),
        airshedBand: isModelled ? (forecastTarget?.aqiBand ?? 'Poor') : (airQuality?.aqiBand ?? 'Poor'),
        timestamp: isModelled ? (forecast?.generatedAt ?? null) : (airQuality?.timestamp ?? null),
        dataSource: isModelled ? 'model_estimate' : 'DEMO_FIXTURE',
      };
    },
    [mode, airQuality, forecast]
  );

  // Setup Documented ML Zones Layers & Centroid Markers
  useEffect(() => {
    if (!mapLoaded || !map.current) return;
    const currentMap = map.current;
    const zonesSourceId = 'pune-documented-zones';

    // 1. Add / Update Zone GeoJSON Source
    if (!currentMap.getSource(zonesSourceId)) {
      currentMap.addSource(zonesSourceId, {
        type: 'geojson',
        data: PUNE_DOCUMENTED_ZONES,
      });

      // Zone fill layer
      currentMap.addLayer({
        id: 'zones-fill',
        type: 'fill',
        source: zonesSourceId,
        paint: {
          'fill-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#0d9488',
            ['boolean', ['feature-state', 'hover'], false],
            '#14b8a6',
            '#0f766e',
          ],
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.4,
            ['boolean', ['feature-state', 'hover'], false],
            0.28,
            0.14,
          ],
        },
      });

      // Zone boundary stroke layer
      currentMap.addLayer({
        id: 'zones-stroke',
        type: 'line',
        source: zonesSourceId,
        paint: {
          'line-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#2dd4bf',
            ['boolean', ['feature-state', 'hover'], false],
            '#14b8a6',
            '#0d9488',
          ],
          'line-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            3.5,
            ['boolean', ['feature-state', 'hover'], false],
            2.5,
            1.8,
          ],
        },
      });

      let hoveredZoneId: number | null = null;

      // Zone hover interactions
      currentMap.on('mousemove', 'zones-fill', (e) => {
        if (!e.features || !e.features[0]) return;
        currentMap.getCanvas().style.cursor = 'pointer';

        if (hoveredZoneId !== null) {
          currentMap.setFeatureState(
            { source: zonesSourceId, id: hoveredZoneId },
            { hover: false }
          );
        }

        const feature = e.features[0];
        hoveredZoneId = feature.id as number;
        currentMap.setFeatureState(
          { source: zonesSourceId, id: hoveredZoneId },
          { hover: true }
        );

        const props = feature.properties as {
          zone_id: string;
          name: string;
          description: string;
          cameraCount: number;
          nearestStation: string;
        };

        const html = `
          <div style="padding: 8px 12px; font-family: var(--font-sans); font-size: 12px; color: var(--color-text-primary); line-height: 1.4;">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
              <span style="font-weight: 700; font-size: 13px;">${props.name}</span>
              <span style="font-size: 10px; padding: 1px 5px; border-radius: 3px; background: rgba(13,148,136,0.2); color: #0d9488; font-weight: 600;">ML Zone</span>
            </div>
            <div style="color: var(--color-text-secondary); margin-bottom: 4px; font-size: 11px;">${props.description}</div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; border-top: 1px solid var(--color-border); padding-top: 4px; margin-top: 4px;">
              <span style="color: var(--color-text-muted);">CCTV Streams:</span>
              <span style="font-weight: 600; color: var(--color-teal);">${props.cameraCount} Cameras</span>
            </div>
            <div style="color: var(--color-text-muted); font-size: 10px; margin-top: 3px;">Click to inspect verified telemetry</div>
          </div>
        `;

        if (hoverPopupRef.current) {
          hoverPopupRef.current.setLngLat(e.lngLat).setHTML(html).addTo(currentMap);
        }
      });

      currentMap.on('mouseleave', 'zones-fill', () => {
        currentMap.getCanvas().style.cursor = '';
        if (hoveredZoneId !== null) {
          currentMap.setFeatureState(
            { source: zonesSourceId, id: hoveredZoneId },
            { hover: false }
          );
          hoveredZoneId = null;
        }
        hoverPopupRef.current?.remove();
      });

      // Zone click interaction
      currentMap.on('click', 'zones-fill', (e) => {
        if (!e.features || !e.features[0]) return;
        const feature = e.features[0];
        const rawProps = feature.properties as { zone_id: string };
        const zoneObj = ZONE_LOOKUP[rawProps.zone_id];
        if (zoneObj) {
          onSelectEntity(buildZoneEntity(zoneObj));
        }
      });
    }

    // 2. Add / Refresh HTML Centroid Markers for the 3 documented ML Chowks
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    DOCUMENTED_ZONES_LIST.forEach((zone) => {
      const isSelected =
        selectedEntity?.type === 'zone' && selectedEntity.zone.zone_id === zone.zone_id;

      const el = document.createElement('div');
      el.className = 'zone-map-marker';
      el.style.display = 'flex';
      el.style.alignItems = 'center';
      el.style.gap = '5px';
      el.style.padding = '4px 8px';
      el.style.borderRadius = '16px';
      el.style.background = isSelected ? '#0d9488' : 'rgba(26, 25, 23, 0.9)';
      el.style.color = '#FFFFFF';
      el.style.border = isSelected ? '2px solid #2dd4bf' : '1px solid rgba(13, 148, 136, 0.6)';
      el.style.boxShadow = isSelected
        ? '0 0 12px rgba(45, 212, 191, 0.8)'
        : '0 2px 6px rgba(0,0,0,0.4)';
      el.style.cursor = 'pointer';
      el.style.fontSize = '11px';
      el.style.fontWeight = '600';
      el.style.fontFamily = 'var(--font-sans)';
      el.style.userSelect = 'none';
      el.style.transition = 'all 150ms ease';
      el.style.whiteSpace = 'nowrap';
      el.innerHTML = `
        <span style="width: 7px; height: 7px; border-radius: 50%; background: ${isSelected ? '#FFFFFF' : '#2dd4bf'};"></span>
        <span>${zone.name}</span>
        <span style="font-size: 9px; opacity: 0.85; font-family: var(--font-mono); background: rgba(255,255,255,0.15); padding: 1px 4px; border-radius: 4px;">${zone.cameraCount}c</span>
      `;

      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.08)';
      });
      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1.0)';
      });
      el.addEventListener('click', (ev) => {
        ev.stopPropagation();
        onSelectEntity(buildZoneEntity(zone));
      });

      const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([zone.longitude, zone.latitude])
        .addTo(currentMap);

      markersRef.current.push(marker);
    });
  }, [mapLoaded, selectedEntity, onSelectEntity, buildZoneEntity]);

  // Synchronize zone feature states with selectedEntity
  useEffect(() => {
    if (!mapLoaded || !map.current) return;
    const currentMap = map.current;
    const sourceId = 'pune-documented-zones';
    if (!currentMap.getSource(sourceId)) return;

    DOCUMENTED_ZONES_LIST.forEach((zone, index) => {
      const featureId = index + 1;
      const isSelected =
        selectedEntity?.type === 'zone' && selectedEntity.zone.zone_id === zone.zone_id;
      currentMap.setFeatureState(
        { source: sourceId, id: featureId },
        { selected: isSelected }
      );
    });
  }, [mapLoaded, selectedEntity]);

  // Hotspots Heatmap & Interactive Points
  useEffect(() => {
    if (!mapLoaded || !map.current || !geoJson) return;
    const currentMap = map.current;
    const sourceId = 'hotspots-source';

    if (currentMap.getSource(sourceId)) {
      (currentMap.getSource(sourceId) as maplibregl.GeoJSONSource).setData(geoJson);
    } else {
      currentMap.addSource(sourceId, {
        type: 'geojson',
        data: geoJson,
      });

      // Heatmap layer for pollution intensity
      currentMap.addLayer(
        {
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
              0.2, 'rgba(74, 222, 128, 0.6)',  // Good (<= 50)
              0.4, 'rgba(250, 204, 21, 0.7)',  // Moderate (<= 100)
              0.6, 'rgba(251, 146, 60, 0.8)',  // Poor (<= 200)
              0.8, 'rgba(239, 68, 68, 0.9)',   // Very Poor (<= 300)
              1, 'rgba(153, 27, 27, 1)'        // Severe (> 300)
            ],
            'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 11, 22, 15, 52],
            'heatmap-opacity': mode === 'observed' ? 0.8 : 0.55,
          },
        },
        'zones-stroke' // ensure heatmap sits below zone stroke
      );

      // Interactive points layer
      currentMap.addLayer({
        id: 'hotspots-points',
        type: 'circle',
        source: sourceId,
        paint: {
          'circle-radius': [
            'step',
            ['get', 'aqi'],
            6,       // Good
            51, 8,   // Satisfactory / Moderate
            101, 10, // Poor
            201, 12, // Very Poor
            301, 14  // Severe
          ],
          'circle-color': [
            'step',
            ['get', 'aqi'],
            '#4ADE80',
            51, '#FACC15',
            101, '#FB923C',
            201, '#EF4444',
            301, '#991B1B'
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#1a1917',
        },
      });

      // Hotspot hover interaction
      currentMap.on('mouseenter', 'hotspots-points', (e) => {
        if (!e.features || !e.features[0]) return;
        currentMap.getCanvas().style.cursor = 'pointer';

        const feature = e.features[0];
        const geom = feature.geometry as GeoJSON.Point;
        const coordinates = geom.coordinates.slice() as [number, number];

        const rawProps = feature.properties as unknown as Record<string, unknown>;
        const props = (typeof rawProps === 'string'
          ? JSON.parse(rawProps)
          : rawProps) as HotspotProperties;

        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
          coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        const html = `
          <div style="padding: 8px 12px; font-family: var(--font-sans); font-size: 12px; color: var(--color-text-primary); line-height: 1.4;">
            <div style="font-weight: 700; margin-bottom: 4px; font-size: 13px;">${props.name}</div>
            <div style="color: var(--color-text-secondary); margin-bottom: 2px;">AQI: <span style="color: var(--color-text-primary); font-weight: 600;">${props.aqi}</span> (${props.aqiBand})</div>
            <div style="color: var(--color-text-secondary); margin-bottom: 4px;">PM2.5: <span style="color: var(--color-text-primary); font-weight: 600;">${props.pm25}</span> <span style="color: var(--color-text-muted);">µg/m³</span></div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; border-top: 1px solid var(--color-border); padding-top: 4px; margin-top: 4px;">
              <span style="color: var(--color-text-muted); text-transform: uppercase;">Driver: ${props.dominantDriver}</span>
              <span style="color: var(--color-modelled); font-weight: 600;">${props.dataSource}</span>
            </div>
          </div>
        `;

        if (hoverPopupRef.current) {
          hoverPopupRef.current.setLngLat(coordinates).setHTML(html).addTo(currentMap);
        }
      });

      currentMap.on('mouseleave', 'hotspots-points', () => {
        currentMap.getCanvas().style.cursor = '';
        hoverPopupRef.current?.remove();
      });

      // Hotspot click interaction
      currentMap.on('click', 'hotspots-points', (e: maplibregl.MapLayerMouseEvent) => {
        if (!e.features || !e.features[0]) return;
        const feature = e.features[0];
        const geom = feature.geometry as GeoJSON.Point;
        const rawProps = feature.properties as unknown as Record<string, unknown>;
        const props = (typeof rawProps === 'string'
          ? JSON.parse(rawProps)
          : rawProps) as HotspotProperties;

        const hotspotEntity: SelectedMapEntity = {
          type: 'hotspot',
          id: props.id,
          name: props.name,
          locality: props.locality,
          latitude: geom.coordinates[1],
          longitude: geom.coordinates[0],
          pm25: props.pm25,
          aqi: props.aqi,
          aqiBand: props.aqiBand,
          dominantDriver: props.dominantDriver,
          intensity: props.intensity,
          timestamp: geoJson.metadata.generatedAt,
          dataSource: props.dataSource,
        };

        onSelectEntity(hotspotEntity);
      });

      // Map canvas click (blank area deselects)
      currentMap.on('click', (e: maplibregl.MapMouseEvent) => {
        const features = currentMap.queryRenderedFeatures(e.point, {
          layers: ['hotspots-points', 'zones-fill'],
        });
        if (!features || features.length === 0) {
          onSelectEntity(null);
        }
      });
    }

    // Update heatmap opacity & line dasharray when mode changes
    if (currentMap.getLayer('hotspots-heatmap')) {
      const opacity = mode === 'observed' ? 0.8 : 0.55;
      currentMap.setPaintProperty('hotspots-heatmap', 'heatmap-opacity', opacity);
    }
    if (currentMap.getLayer('zones-stroke')) {
      // Modelled uses dashed indicator; observed uses solid indicator
      if (mode === 'modelled') {
        currentMap.setPaintProperty('zones-stroke', 'line-dasharray', [2, 2]);
      } else {
        currentMap.setPaintProperty('zones-stroke', 'line-dasharray', [1, 0]);
      }
    }
  }, [mapLoaded, geoJson, mode, onSelectEntity]);

  // Fly / Fit to selected zone or hotspot
  useEffect(() => {
    if (!mapLoaded || !map.current) return;
    const currentMap = map.current;

    if (!selectedEntity) {
      currentMap.flyTo({
        center: PUNE_CENTER,
        zoom: DEFAULT_ZOOM,
        essential: true,
        duration: 700,
      });
      return;
    }

    if (selectedEntity.type === 'zone') {
      currentMap.flyTo({
        center: [selectedEntity.zone.longitude, selectedEntity.zone.latitude],
        zoom: 14.8,
        essential: true,
        duration: 800,
      });
    } else if (selectedEntity.type === 'hotspot') {
      currentMap.flyTo({
        center: [selectedEntity.longitude, selectedEntity.latitude],
        zoom: 14.0,
        essential: true,
        duration: 800,
      });
    }
  }, [mapLoaded, selectedEntity]);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        background: 'var(--color-bg-base)',
      }}
    >
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
