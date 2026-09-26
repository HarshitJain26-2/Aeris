import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList, CartesianGrid } from 'recharts';
import type { ScenarioResult } from '../../types/scenario';

interface ScenarioCompareProps {
  result: ScenarioResult;
}

interface ScenarioTooltipPayloadItem {
  payload: {
    name: string;
    pm25: number;
    type: string;
  };
}

interface ScenarioTooltipProps {
  active?: boolean;
  payload?: ScenarioTooltipPayloadItem[];
}

const CustomTooltip: React.FC<ScenarioTooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const { name, pm25 } = payload[0].payload;
    const isChange = name === 'Change';
    const displayVal = isChange ? (pm25 > 0 ? `+${pm25.toFixed(1)}` : pm25.toFixed(1)) : pm25.toFixed(1);

    return (
      <div style={{
        background: '#FFFFFF',
        border: '1px solid #D9E2EC',
        padding: '8px 12px',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(11, 30, 61, 0.08)',
      }}>
        <p style={{ color: '#64748B', fontFamily: 'Inter, sans-serif', fontSize: '12px', marginBottom: '4px', fontWeight: 400, margin: 0 }}>{name}</p>
        <p style={{ color: '#0B1F3A', fontFamily: 'Inter, sans-serif', fontSize: '14px', fontWeight: 700, margin: '4px 0 0 0' }}>
          {displayVal} <span style={{ fontSize: '12px', color: '#64748B', fontWeight: 400 }}>µg/m³</span>
        </p>
      </div>
    );
  }
  return null;
};

export const ScenarioCompare: React.FC<ScenarioCompareProps> = ({ result }) => {
  const signedChange = result.modelled.pm25 - result.baseline.pm25;
  const isReduction = signedChange <= 0;
  const changeColor = isReduction ? '#16A34A' : '#EF4444';

  const data = [
    {
      name: 'Baseline',
      pm25: Number(result.baseline.pm25.toFixed(1)),
      type: 'baseline'
    },
    {
      name: 'Scenario',
      pm25: Number(result.modelled.pm25.toFixed(1)),
      type: 'scenario'
    },
    {
      name: 'Change',
      pm25: Number(signedChange.toFixed(1)),
      type: 'change'
    }
  ];

  return (
    <div style={{ width: '100%', height: '220px', minWidth: 0, flexShrink: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 24, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <pattern id="pattern-change" width="6" height="6" patternTransform="rotate(-45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="6" stroke={changeColor} strokeWidth="2" opacity={0.8} />
            </pattern>
          </defs>
          <CartesianGrid stroke="#E2E8F0" vertical={false} />
          <XAxis 
            dataKey="name" 
            stroke="#64748B" 
            fontSize={12} 
            fontFamily="Inter, sans-serif"
            tick={{ fill: '#64748B' }} 
            axisLine={{ stroke: '#D9E2EC' }}
            tickLine={false}
          />
          <YAxis 
            stroke="#64748B" 
            fontSize={12} 
            fontFamily="Inter, sans-serif"
            tick={{ fill: '#64748B' }} 
            axisLine={false} 
            tickLine={false} 
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.02)' }} />
          <Bar 
            dataKey="pm25" 
            maxBarSize={40} 
            isAnimationActive={true} 
            animationDuration={700}
            animationEasing="ease-out"
          >
            <LabelList 
              dataKey="pm25" 
              position="top" 
              fill="#0B1F3A" 
              fontSize={14} 
              fontWeight={700} 
              fontFamily="Inter, sans-serif"
              formatter={(val: number) => val > 0 && data.find(d => d.pm25 === val)?.type === 'change' ? `+${val}` : val}
            />
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={
                  entry.type === 'baseline' ? '#14A394' : 
                  entry.type === 'scenario' ? '#1769D2' : 
                  'url(#pattern-change)'
                }
                stroke={
                  entry.type === 'baseline' ? '#14A394' : 
                  entry.type === 'scenario' ? '#1769D2' : 
                  changeColor
                }
                strokeWidth={2}
                strokeDasharray={entry.type === 'scenario' ? '4 4' : 'none'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
