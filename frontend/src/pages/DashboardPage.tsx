import React, { useState } from 'react';
import { ObservedPanel } from '../components/panels/ObservedPanel';
import { ForecastPanel } from '../components/panels/ForecastPanel';
import { DriverPanel } from '../components/panels/DriverPanel';
import { ScenarioPanel } from '../components/panels/ScenarioPanel';
import { HotspotMap } from '../components/map/HotspotMap';
import { LayerToggle } from '../components/map/LayerToggle';
import { MapLegend } from '../components/map/MapLegend';
import { ZoneInfoPanel } from '../components/panels/ZoneInfoPanel';
import { useHotspots } from '../hooks/useHotspots';
import type { HotspotFeature } from '../types/hotspot';

export const DashboardPage: React.FC = () => {
  const [mapMode, setMapMode] = useState<'observed' | 'modelled'>('observed');
  const [selectedZone, setSelectedZone] = useState<HotspotFeature | null>(null);
  const { data: hotspots, loading: hotspotsLoading } = useHotspots();

  return (
    <div className="dashboard-grid h-full w-full p-4 gap-4 grid grid-cols-1 xl:[grid-template-columns:minmax(280px,320px)_minmax(400px,1fr)_minmax(320px,360px)] overflow-y-auto xl:overflow-hidden">
      {/* LEFT COLUMN: Data & Analysis */}
      <div className="flex flex-col gap-4 xl:overflow-y-auto xl:pr-1 min-w-0 order-2 xl:order-1 xl:pb-5">
        <ObservedPanel />
        <ForecastPanel />
        <DriverPanel />
      </div>

      {/* CENTER COLUMN: Map Hero & Zone Panel */}
      <div className="flex flex-col gap-4 min-h-[600px] xl:h-full xl:min-h-0 min-w-0 order-1 xl:order-2">
        <div className="relative flex-1 rounded-xl overflow-hidden border border-border shadow-card bg-bg-surface min-h-[400px] xl:min-h-0">
          <HotspotMap 
            geoJson={hotspots} 
            mode={mapMode} 
            loading={hotspotsLoading}
            onZoneSelect={setSelectedZone} 
          />
          <LayerToggle mode={mapMode} onChange={setMapMode} />
          <MapLegend />
        </div>
        
        {/* New Persistent Zone Panel */}
        <ZoneInfoPanel feature={selectedZone} />
      </div>

      {/* RIGHT COLUMN: Scenarios & Legend */}
      <div className="flex flex-col gap-4 xl:h-full min-w-0 xl:overflow-y-auto xl:pr-1 order-3 xl:pb-5">
        <ScenarioPanel />
      </div>
    </div>
  );
};
