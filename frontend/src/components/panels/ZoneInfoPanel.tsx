import React from 'react';
import { Card } from '../ui/Card';
import { AqiBadge } from '../ui/AqiBadge';
import { EmptyState } from '../ui/EmptyState';
import { ObservedTag } from '../status/ObservedTag';
import { ModelledTag } from '../status/ModelledTag';
import type { SelectedMapEntity } from '../../types/zone';
import { Camera, MapPin, Radio, Car, Factory, Home, AlertCircle } from 'lucide-react';

interface ZoneInfoPanelProps {
  selectedEntity: SelectedMapEntity | null;
  mode?: 'observed' | 'modelled';
}

export const ZoneInfoPanel: React.FC<ZoneInfoPanelProps> = ({
  selectedEntity,
  mode = 'observed',
}) => {
  if (!selectedEntity) {
    return (
      <Card className="p-4 flex items-center justify-center min-h-[160px]">
        <EmptyState
          title="Select an Urban Zone or Hotspot"
          hint="Click on Alankar Chowk, Jehangir Chowk, RTO Chowk, or any hotspot point on the map to inspect verified coordinates, traffic streams, and provenance."
        />
      </Card>
    );
  }

  if (selectedEntity.type === 'zone') {
    const { zone, airshedPm25, airshedAqi, airshedBand, timestamp, dataSource } = selectedEntity;

    return (
      <Card className="p-0 overflow-hidden min-h-[190px] border border-border">
        <div className="p-5 flex flex-col gap-4">
          {/* Header */}
          <div className="flex flex-wrap justify-between items-start gap-2 border-b border-border pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-text-primary m-0 tracking-tight">
                  {zone.name}
                </h2>
                <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-bg-elevated text-text-muted border border-border">
                  {zone.zone_id}
                </span>
              </div>
              <p className="text-xs text-text-secondary m-0 mt-1">
                {zone.description} • <span className="text-text-muted">{zone.areaType}</span>
              </p>
            </div>

            <div className="flex items-center gap-2">
              {dataSource === 'DEMO_FIXTURE' ? (
                <span className="text-[10px] font-semibold px-2 py-1 rounded bg-bg-elevated border border-border text-amber-500 uppercase tracking-wider">
                  Demo Fixture
                </span>
              ) : mode === 'modelled' ? (
                <ModelledTag label="Modeled Airshed" />
              ) : (
                <ObservedTag label="Observed Traffic" />
              )}
            </div>
          </div>

          {/* Verified Fields Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* GPS Coordinates */}
            <div className="flex flex-col gap-1 p-3 rounded-lg bg-bg-base border border-border">
              <div className="flex items-center gap-1.5 text-text-muted text-[11px] uppercase tracking-wider font-semibold">
                <MapPin size={12} className="text-teal" />
                <span>Coordinates</span>
              </div>
              <div className="font-mono text-xs font-semibold text-text-primary mt-1">
                {zone.latitude.toFixed(4)}° N, {zone.longitude.toFixed(4)}° E
              </div>
              <span className="text-[10px] text-text-secondary">WGS84 Junction Center</span>
            </div>

            {/* Monitored CCTV Cameras */}
            <div className="flex flex-col gap-1 p-3 rounded-lg bg-bg-base border border-border">
              <div className="flex items-center gap-1.5 text-text-muted text-[11px] uppercase tracking-wider font-semibold">
                <Camera size={12} className="text-teal" />
                <span>Traffic CCTV Feeds</span>
              </div>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="font-mono text-xs font-semibold text-text-primary">
                  {zone.cameraCount} Streams
                </span>
                <span className="text-[10px] font-mono text-teal bg-teal/10 px-1.5 py-0.5 rounded border border-teal/20">
                  {zone.cameras.join(', ')}
                </span>
              </div>
              <span className="text-[10px] text-text-secondary">Ground CCTV Vehicle Counts</span>
            </div>

            {/* Air Quality Telemetry Status */}
            <div className="flex flex-col gap-1 p-3 rounded-lg bg-bg-base border border-border">
              <div className="flex items-center gap-1.5 text-text-muted text-[11px] uppercase tracking-wider font-semibold">
                <Radio size={12} className="text-amber-500" />
                <span>Airshed PM2.5 Reference</span>
              </div>
              {airshedPm25 != null ? (
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono text-xs font-semibold text-text-primary">
                    {airshedPm25} <span className="text-[10px] text-text-muted font-normal">µg/m³</span>
                  </span>
                  {airshedAqi != null && (
                    <AqiBadge aqi={airshedAqi} band={airshedBand ?? undefined} size="sm" />
                  )}
                </div>
              ) : (
                <div className="text-xs text-text-secondary font-mono mt-1">
                  City SAFAR Reference
                </div>
              )}
              <span className="text-[10px] text-text-secondary truncate" title={zone.nearestStation}>
                {zone.nearestStation} (~{zone.distanceToStationKm} km)
              </span>
            </div>
          </div>

          {/* Scientific Provenance Disclosure */}
          <div className="flex items-start gap-2 p-2.5 rounded-lg bg-bg-elevated border border-border/70 text-[11px] text-text-secondary">
            <AlertCircle size={14} className="text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-text-primary">Provenance Disclosure: </span>
              CCTV traffic counts are verified ground observations. Individual junctions do not possess dedicated CAAQMS monitors; atmospheric PM2.5 is mapped to the regional airshed ({mode === 'modelled' ? 'CAMS Atmospheric Model Forecast' : 'Shivajinagar IITM SAFAR Station'}).
              {timestamp && (
                <span className="ml-2 font-mono text-[10px] text-text-muted">
                  Updated: {new Date(timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // Hotspot feature selected
  const { name, locality, pm25, aqi, aqiBand, dominantDriver, latitude, longitude, timestamp, dataSource } = selectedEntity;

  const getDriverIcon = (driver: string) => {
    switch (driver) {
      case 'Traffic': return <Car size={13} className="text-amber-500" />;
      case 'Industrial': return <Factory size={13} className="text-orange-500" />;
      case 'Residential/Biomass': return <Home size={13} className="text-teal" />;
      default: return null;
    }
  };

  return (
    <Card className="p-0 overflow-hidden min-h-[190px] border border-border">
      <div className="p-5 flex flex-col gap-4">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-start gap-2 border-b border-border pb-3">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-text-primary m-0 tracking-tight">{name}</h2>
              <span className="text-xs text-text-secondary font-medium">({locality})</span>
            </div>
            <p className="text-xs text-text-muted m-0 mt-0.5">
              Spatial Hotspot Telemetry Analysis
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-semibold px-2 py-1 rounded bg-bg-elevated border border-border text-amber-500 uppercase tracking-wider">
              {dataSource === 'DEMO_FIXTURE' ? 'DEMO FIXTURE' : dataSource}
            </span>
          </div>
        </div>

        {/* Verified Fields Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* PM2.5 */}
          <div className="flex flex-col gap-1 p-3 rounded-lg bg-bg-base border border-border">
            <span className="text-text-muted text-[11px] uppercase tracking-wider font-semibold">
              PM2.5 Intensity
            </span>
            <div className="font-mono text-sm font-semibold text-text-primary mt-1">
              {pm25} <span className="text-[10px] text-text-muted font-normal">µg/m³</span>
            </div>
            <span className="text-[10px] text-text-secondary">Particulate Matter 2.5</span>
          </div>

          {/* AQI */}
          <div className="flex flex-col gap-1 p-3 rounded-lg bg-bg-base border border-border">
            <span className="text-text-muted text-[11px] uppercase tracking-wider font-semibold">
              India NAQI
            </span>
            <div className="mt-1">
              <AqiBadge aqi={aqi} band={aqiBand} size="sm" />
            </div>
            <span className="text-[10px] text-text-secondary">CPCB 6-Band Standard</span>
          </div>

          {/* Dominant Driver */}
          <div className="flex flex-col gap-1 p-3 rounded-lg bg-bg-base border border-border">
            <span className="text-text-muted text-[11px] uppercase tracking-wider font-semibold">
              Dominant Driver
            </span>
            <div className="flex items-center gap-1.5 mt-1">
              {getDriverIcon(dominantDriver)}
              <span className="text-xs font-semibold text-text-primary">{dominantDriver}</span>
            </div>
            <span className="text-[10px] text-text-secondary">Source Attribution</span>
          </div>

          {/* Coordinates */}
          <div className="flex flex-col gap-1 p-3 rounded-lg bg-bg-base border border-border">
            <span className="text-text-muted text-[11px] uppercase tracking-wider font-semibold">
              Coordinates
            </span>
            <div className="font-mono text-xs font-semibold text-text-primary mt-1">
              {latitude.toFixed(4)}° N, {longitude.toFixed(4)}° E
            </div>
            <span className="text-[10px] text-text-secondary">WGS84 Point Location</span>
          </div>
        </div>

        {/* Provenance note */}
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-bg-elevated border border-border/70 text-[11px] text-text-secondary">
          <AlertCircle size={14} className="text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-text-primary">Fixture Provenance: </span>
            This hotspot reading is provided by the development fixture dataset (<code>hotspots.json</code>). Zero simulated sensor values are fabricated.
            {timestamp && (
              <span className="ml-2 font-mono text-[10px] text-text-muted">
                Generated: {new Date(timestamp).toLocaleDateString('en-IN')}
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};
