import React, { useState } from 'react';
import { ObservedPanel } from '../components/panels/ObservedPanel';
import { ForecastPanel } from '../components/panels/ForecastPanel';
import { DriverPanel } from '../components/panels/DriverPanel';
import { ScenarioPanel } from '../components/panels/ScenarioPanel';
import { HotspotMap } from '../components/map/HotspotMap';
import { LayerToggle } from '../components/map/LayerToggle';
import { MapLegend } from '../components/map/MapLegend';
import { ZonePopup } from '../components/map/ZonePopup';
import { useHotspots } from '../hooks/useHotspots';
import type { HotspotFeature } from '../types/hotspot';

export const DashboardPage: React.FC = () => {
  const [mapMode, setMapMode] = useState<'observed' | 'modelled'>('observed');
  const [selectedZone, setSelectedZone] = useState<HotspotFeature | null>(null);
  const { data: hotspots } = useHotspots();

  return (
    <div className="dashboard-grid h-full w-full p-4 gap-4 overflow-hidden" style={{
      display: 'grid',
      gridTemplateColumns: 'minmax(280px, 320px) minmax(400px, 1fr) minmax(320px, 360px)',
      gridTemplateRows: '1fr',
      height: '100%',
    }}>
      {/* LEFT COLUMN: Data & Analysis */}
      <div className="flex flex-col gap-4 overflow-y-auto pr-1 min-w-0" style={{ paddingBottom: '20px' }}>
        <ObservedPanel />
        <ForecastPanel />
        <DriverPanel />
      </div>

      {/* CENTER COLUMN: Map Hero */}
      <div className="relative rounded-xl overflow-hidden border border-border shadow-card bg-bg-surface h-full min-w-0">
        <HotspotMap 
          geoJson={hotspots} 
          mode={mapMode} 
          onZoneSelect={setSelectedZone} 
        />
        <LayerToggle mode={mapMode} onChange={setMapMode} />
        <MapLegend />
        {selectedZone && (
          <ZonePopup feature={selectedZone} onClose={() => setSelectedZone(null)} />
        )}
      </div>

      {/* RIGHT COLUMN: Scenarios */}
      <div className="h-full min-w-0 overflow-y-auto">
        <ScenarioPanel />
      </div>
    </div>
  );
};
