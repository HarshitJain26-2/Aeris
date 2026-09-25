import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Skeleton } from '../ui/Skeleton';
import type { DriverAttribution } from '../../types/source';

interface DriverDonutProps {
  drivers: DriverAttribution[];
  loading?: boolean;
}

interface DriverTooltipPayloadItem {
  payload: DriverAttribution & { fill?: string };
}

interface DriverTooltipProps {
  active?: boolean;
  payload?: DriverTooltipPayloadItem[];
}

const CustomTooltip: React.FC<DriverTooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div style={{
        background: 'var(--color-bg-elevated)',
        border: '1px solid var(--color-border)',
        padding: '8px 12px',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-pop)',
        maxWidth: '180px'
      }}>
        <p style={{ color: 'var(--color-text-primary)', fontSize: 'var(--text-sm)', fontWeight: 600 }}>
          {data.category}
        </p>
        <p style={{ color: payload[0].payload.fill || 'var(--color-text-primary)', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-mono)', fontWeight: 600, margin: '2px 0 6px' }}>
          ~{data.estimatedPct}% <span style={{ fontSize: '0.85em', color: 'var(--color-text-muted)', fontWeight: 400 }}>(DEMO)</span>
        </p>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-xs)', lineHeight: 1.3 }}>
          {data.description}
        </p>
      </div>
    );
  }
  return null;
};

export const DriverDonut: React.FC<DriverDonutProps> = ({ drivers, loading }) => {
  if (loading) {
    return (
      <div style={{ width: '100px', height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Skeleton width="100px" height="100px" borderRadius="50%" style={{ opacity: 0.4 }} />
      </div>
    );
  }
  if (!drivers || drivers.length === 0) return null;

  const CATEGORY_COLORS: Record<string, string> = {
    'Traffic': 'var(--chart-cat-1)',
    'Industrial': 'var(--chart-cat-2)',
    'Residential/Biomass': 'var(--chart-cat-3)',
  };

  return (
    <div style={{ width: '100px', height: '100px', position: 'relative' }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={drivers}
            dataKey="estimatedPct"
            cx="50%"
            cy="50%"
            innerRadius={30}
            outerRadius={45}
            stroke="var(--color-bg-surface)"
            strokeWidth={2}
            isAnimationActive={true}
          >
            {drivers.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.category] || 'var(--color-border)'} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
