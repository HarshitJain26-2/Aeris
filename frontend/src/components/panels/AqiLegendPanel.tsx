import React from 'react';
import { Card } from '../ui/Card';

export const AqiLegendPanel: React.FC = () => {
  const bands = [
    { label: 'Good', range: '0-50', color: 'var(--aqi-good)' },
    { label: 'Satisfactory', range: '51-100', color: '#84B02E' },
    { label: 'Moderate', range: '101-200', color: 'var(--aqi-moderate)' },
    { label: 'Poor', range: '201-300', color: 'var(--aqi-poor)' },
    { label: 'Very Poor', range: '301-400', color: 'var(--aqi-severe)' },
    { label: 'Severe', range: '401-500', color: 'var(--aqi-hazardous)' },
  ];

  return (
    <Card className="p-5 flex flex-col gap-4 shrink-0">
      <div>
        <h3 className="text-sm font-bold text-text-primary m-0 uppercase tracking-wider">India CPCB AQI</h3>
        <p className="text-xs text-text-secondary m-0 mt-1">Air Quality Index Category Reference</p>
      </div>

      <div className="flex flex-col gap-3">
        {bands.map((band) => (
          <div key={band.label} className="flex items-center gap-3">
            <div 
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: band.color,
                boxShadow: '0 0 0 1px rgba(0,0,0,0.1) inset'
              }}
            />
            <div className="flex-1 flex justify-between items-center text-sm">
              <span className="font-medium text-text-primary">{band.label}</span>
              <span className="text-text-secondary font-mono">{band.range}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
