import React from 'react';
import { Card } from '../ui/Card';
import { AqiBadge } from '../ui/AqiBadge';
import { EmptyState } from '../ui/EmptyState';
import type { HotspotFeature } from '../../types/hotspot';

interface ZoneInfoPanelProps {
  feature: HotspotFeature | null;
}

export const ZoneInfoPanel: React.FC<ZoneInfoPanelProps> = ({ feature }) => {
  if (!feature) {
    return (
      <Card className="p-4 flex items-center justify-center min-h-[160px]">
        <EmptyState title="Select a zone on the map" hint="Click on any hotspot to view detailed zone information." />
      </Card>
    );
  }

  const { name, locality, pm25, aqi, aqiBand, dominantDriver } = feature.properties;

  // Derive/Mock missing fields for UI display
  const areaType = dominantDriver === 'Traffic' ? 'Commercial / Transport' :
                   dominantDriver === 'Industrial' ? 'Industrial Zone' : 'Residential / Mixed';
  const temp = '28°C';
  const humidity = '65%';
  const trafficIntensity = dominantDriver === 'Traffic' ? 'High' : 'Moderate';

  return (
    <Card className="p-0 overflow-hidden flex flex-row min-h-[200px]">
      <div className="flex-1 p-5 flex flex-col gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary m-0">{name}</h2>
          <p className="text-sm text-text-secondary m-0">{locality} • {areaType}</p>
        </div>

        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          <div className="flex justify-between items-center border-b border-border pb-1">
            <span className="text-xs text-text-secondary uppercase tracking-wider">PM2.5</span>
            <span className="font-mono font-semibold text-text-primary">{pm25} <span className="text-[10px] text-text-muted">µg/m³</span></span>
          </div>
          
          <div className="flex justify-between items-center border-b border-border pb-1">
            <span className="text-xs text-text-secondary uppercase tracking-wider">AQI</span>
            <AqiBadge aqi={aqi} band={aqiBand} size="sm" />
          </div>

          <div className="flex justify-between items-center border-b border-border pb-1">
            <span className="text-xs text-text-secondary uppercase tracking-wider">Temperature</span>
            <span className="font-mono font-semibold text-text-primary">{temp}</span>
          </div>

          <div className="flex justify-between items-center border-b border-border pb-1">
            <span className="text-xs text-text-secondary uppercase tracking-wider">Humidity</span>
            <span className="font-mono font-semibold text-text-primary">{humidity}</span>
          </div>

          <div className="flex justify-between items-center border-b border-border pb-1 col-span-2">
            <span className="text-xs text-text-secondary uppercase tracking-wider">Traffic Intensity</span>
            <span className="font-semibold text-text-primary">{trafficIntensity}</span>
          </div>
        </div>
      </div>
      
      <div className="w-[200px] bg-bg-elevated relative overflow-hidden hidden sm:block shrink-0 border-l border-border">
        <img 
          src="/placeholder-zone.jpg" 
          alt={`Photo of ${name}`}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
        {/* Soft gradient overlay for aesthetics to blend it slightly */}
        <div 
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(to right, var(--color-bg-surface), transparent 30%)',
            pointerEvents: 'none'
          }}
        />
      </div>
    </Card>
  );
};
