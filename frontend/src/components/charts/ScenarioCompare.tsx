import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { ScenarioResult } from '../../types/scenario';

interface ScenarioCompareProps {
  result: ScenarioResult;
}

export const ScenarioCompare: React.FC<ScenarioCompareProps> = ({ result }) => {
  const data = [
    {
      name: 'Baseline',
      pm25: result.baseline.pm25,
      type: 'baseline'
    },
    {
      name: 'Modelled',
      pm25: result.modelled.pm25,
      type: 'modelled'
    }
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const { name, pm25, type } = payload[0].payload;
      return (
        <div style={{
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border)',
          padding: '8px 12px',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-pop)',
        }}>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-xs)', marginBottom: '4px' }}>{name}</p>
          <p style={{ color: 'var(--color-text-primary)', fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
            {pm25} <span style={{ fontSize: '0.85em', color: 'var(--color-text-muted)', fontWeight: 400 }}>µg/m³</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: '140px', minWidth: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <XAxis 
            dataKey="name" 
            stroke="var(--color-text-muted)" 
            fontSize={10} 
            tick={{ fill: 'var(--color-text-muted)' }} 
            axisLine={false} 
            tickLine={false}
          />
          <YAxis 
            stroke="var(--color-text-muted)" 
            fontSize={10} 
            tick={{ fill: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }} 
            axisLine={false} 
            tickLine={false} 
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
          <Bar dataKey="pm25" radius={[4, 4, 0, 0]} maxBarSize={40} isAnimationActive={true} animationDuration={600}>
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill="transparent"
                stroke={entry.type === 'baseline' ? 'var(--color-observed)' : 'var(--color-modelled)'}
                strokeWidth={2}
                strokeDasharray={entry.type === 'modelled' ? '4 3' : 'none'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
