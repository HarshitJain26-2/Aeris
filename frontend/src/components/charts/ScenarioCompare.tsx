import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';
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

interface CustomLabelProps {
  x?: number | string;
  y?: number | string;
  width?: number | string;
  height?: number | string;
  value?: number | string;
  index?: number;
}

const renderCustomLabel = (props: CustomLabelProps) => {
  const x = Number(props.x ?? 0);
  const y = Number(props.y ?? 0);
  const width = Number(props.width ?? 0);
  const height = Number(props.height ?? 0);
  const { value, index } = props;
  if (value === undefined || value === null) return null;
  const numValue = typeof value === 'number' ? value : Number(value);
  if (isNaN(numValue)) return null;

  // Baseline and Scenario labels
  if (index === 0 || index === 1) {
    return (
      <text
        x={x + width / 2}
        y={y - 6}
        fill="var(--color-text-primary)"
        textAnchor="middle"
        fontSize={11}
        fontWeight={600}
        fontFamily="var(--font-mono)"
      >
        {numValue.toFixed(1)}
      </text>
    );
  }

  // Change bar label
  if (index === 2) {
    // If the bar magnitude is too small to render cleanly, conditionally hide it
    if (Math.abs(numValue) < 0.05) {
      return null;
    }

    const formatted = numValue > 0 ? `+${numValue.toFixed(1)}` : numValue.toFixed(1);
    const absHeight = Math.abs(height);
    const yPos = numValue >= 0 ? y - 6 : y + absHeight + 14;

    return (
      <text
        x={x + width / 2}
        y={yPos}
        fill="var(--color-text-primary)"
        textAnchor="middle"
        fontSize={11}
        fontWeight={600}
        fontFamily="var(--font-mono)"
      >
        {formatted}
      </text>
    );
  }

  return null;
};

const CustomTooltip: React.FC<ScenarioTooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const { name, pm25 } = payload[0].payload;
    const formattedPm25 = typeof pm25 === 'number'
      ? (name === 'Change' && pm25 > 0 ? `+${pm25}` : `${pm25}`)
      : pm25;
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
          {formattedPm25} <span style={{ fontSize: '0.85em', color: 'var(--color-text-muted)', fontWeight: 400 }}>µg/m³</span>
        </p>
      </div>
    );
  }
  return null;
};

export const ScenarioCompare: React.FC<ScenarioCompareProps> = ({ result }) => {
  const data = [
    {
      name: 'Baseline',
      pm25: result.baseline.pm25,
      type: 'baseline'
    },
    {
      name: 'Scenario',
      pm25: result.modelled.pm25,
      type: 'scenario'
    },
    {
      name: 'Change',
      pm25: result.modelled.pm25 - result.baseline.pm25,
      type: 'change'
    }
  ];

  return (
    <div style={{ width: '100%', height: '180px', minWidth: 0, flexShrink: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 24, right: 10, left: -20, bottom: 24 }}>
          <defs>
            <pattern id="pattern-change" width="6" height="6" patternTransform="rotate(-45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="6" stroke="var(--aqi-good)" strokeWidth="2" opacity={0.8} />
            </pattern>
          </defs>
          <XAxis 
            dataKey="name" 
            stroke="var(--color-text-muted)" 
            fontSize={12} 
            tick={{ fill: 'var(--color-text-muted)' }} 
            axisLine={false} 
            tickLine={false}
          />
          <YAxis 
            stroke="var(--color-text-muted)" 
            fontSize={12} 
            tick={{ fill: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }} 
            axisLine={false} 
            tickLine={false} 
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
          <Bar 
            dataKey="pm25" 
            radius={[4, 4, 0, 0]} 
            maxBarSize={40} 
            isAnimationActive={true} 
            animationDuration={700}
            animationEasing="ease-out"
          >
            <LabelList dataKey="pm25" content={renderCustomLabel} />
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={
                  entry.type === 'baseline' ? 'var(--chart-cat-3)' : 
                  entry.type === 'scenario' ? 'var(--color-accent)' : 
                  'url(#pattern-change)'
                }
                stroke={
                  entry.type === 'baseline' ? 'var(--chart-cat-3)' : 
                  entry.type === 'scenario' ? 'var(--color-accent)' : 
                  'var(--aqi-good)'
                }
                strokeWidth={2}
                strokeDasharray="none"
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
