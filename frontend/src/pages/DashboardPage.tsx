import React, { useState } from 'react';
import { ObservedPanel } from '../components/panels/ObservedPanel';
import { ForecastPanel } from '../components/panels/ForecastPanel';
import { DriverPanel } from '../components/panels/DriverPanel';
import { ScenarioPanel } from '../components/panels/ScenarioPanel';
import { AqiLegendPanel } from '../components/panels/AqiLegendPanel';
import { HotspotMap } from '../components/map/HotspotMap';
import { LayerToggle } from '../components/map/LayerToggle';
import { ZoneSelector } from '../components/map/ZoneSelector';
import { MapLegend } from '../components/map/MapLegend';
import { ZoneInfoPanel } from '../components/panels/ZoneInfoPanel';
import { useHotspots } from '../hooks/useHotspots';
import { useAirQuality } from '../hooks/useAirQuality';
import { useForecast } from '../hooks/useForecast';
import { useZones } from '../hooks/useZones';
import type { SelectedMapEntity } from '../types/zone';

export const DashboardPage: React.FC = () => {
  const [mapMode, setMapMode] = useState<'observed' | 'modelled'>('observed');
  const [selectedEntity, setSelectedEntity] = useState<SelectedMapEntity | null>(null);

  const { data: hotspots } = useHotspots();
  const { data: airQuality } = useAirQuality();
  const { data: forecast } = useForecast();
  const { data: zones } = useZones();

  return (
    <div
      className="dashboard-grid h-full w-full p-4 gap-4 overflow-hidden"
      style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(280px, 320px) minmax(400px, 1fr) minmax(320px, 360px)',
        gridTemplateRows: '1fr',
        height: '100%',
      }}
    >
      {/* LEFT COLUMN: Data & Analysis */}
      <div className="flex flex-col gap-4 overflow-y-auto pr-1 min-w-0" style={{ paddingBottom: '20px' }}>
        <ObservedPanel />
        <ForecastPanel />
        <DriverPanel />
      </div>

      {/* CENTER COLUMN: Map Hero & Zone Panel */}
      <div className="flex flex-col gap-4 h-full min-w-0">
        <div className="relative flex-1 rounded-xl overflow-hidden border border-border shadow-card bg-bg-surface min-h-0">
          <HotspotMap
            geoJson={hotspots}
            mode={mapMode}
            selectedEntity={selectedEntity}
            onSelectEntity={setSelectedEntity}
            airQuality={airQuality}
            forecast={forecast}
          />
          <LayerToggle mode={mapMode} onChange={setMapMode} />
          <ZoneSelector
            zones={zones || []}
            selectedEntity={selectedEntity}
            onSelectZone={(zone) => {
              if (!zone) {
                setSelectedEntity(null);
              } else {
                const isModelled = mapMode === 'modelled';
                const forecastTarget = forecast?.points?.find((p) => p.type === 'forecast');
                setSelectedEntity({
                  type: 'zone',
                  zone,
                  airshedPm25: isModelled ? (forecastTarget?.pm25 ?? 96.1) : (airQuality?.pm25 ?? 94.2),
                  airshedAqi: isModelled ? (forecastTarget?.aqi ?? 215) : (airQuality?.aqi ?? 212),
                  airshedBand: isModelled ? (forecastTarget?.aqiBand ?? 'Poor') : (airQuality?.aqiBand ?? 'Poor'),
                  timestamp: isModelled ? (forecast?.generatedAt ?? null) : (airQuality?.timestamp ?? null),
                  dataSource: isModelled ? 'model_estimate' : 'DEMO_FIXTURE',
                });
              }
            }}
          />
          <MapLegend />
        </div>

        {/* Selected Zone or Hotspot Detail Panel */}
        <ZoneInfoPanel selectedEntity={selectedEntity} mode={mapMode} />
      </div>

      {/* RIGHT COLUMN: Scenarios & Legend */}
      <div className="flex flex-col gap-4 h-full min-w-0 overflow-y-auto pr-1" style={{ paddingBottom: '20px' }}>
        <ScenarioPanel />
        <AqiLegendPanel />
      </div>
    </div>
  );
};
