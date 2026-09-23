import React from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea
} from 'recharts';
import type { ForecastPoint } from '../../types/forecast';
import { CPCB_BANDS } from '../../lib/cpcbAqi';

interface ForecastChartProps {
  data: ForecastPoint[];
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  // Format data for Recharts
  const chartData = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    pm25: d.pm25,
    isForecast: d.type === 'forecast',
    // Split into two lines for styling (solid vs dashed)
    observedPm25: d.type === 'observed' ? d.pm25 : null,
    forecastPm25: d.type === 'forecast' ? d.pm25 : null,
  }));

  // Connect the lines by adding the last observed point to the forecast series
  const reversedIndex = [...chartData].reverse().findIndex(d => !d.isForecast);
  const lastObservedIndex = reversedIndex >= 0 ? chartData.length - 1 - reversedIndex : -1;
  if (lastObservedIndex !== -1 && lastObservedIndex < chartData.length - 1) {
    chartData[lastObservedIndex].forecastPm25 = chartData[lastObservedIndex].observedPm25;
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <div style={{
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border)',
          padding: '8px 12px',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-pop)',
        }}>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-xs)', marginBottom: '4px' }}>{label}</p>
          <p style={{ color: 'var(--color-text-primary)', fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
            {dataPoint.pm25} <span style={{ fontSize: '0.85em', color: 'var(--color-text-muted)', fontWeight: 400 }}>µg/m³</span>
          </p>
          <p style={{ color: dataPoint.isForecast ? 'var(--color-modelled)' : 'var(--color-observed)', fontSize: 'var(--text-xs)', marginTop: '2px' }}>
            {dataPoint.isForecast ? 'Model Estimate' : 'Observed'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: '220px', minWidth: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke="var(--color-text-muted)" 
            fontSize={10} 
            tickMargin={8} 
            tick={{ fill: 'var(--color-text-muted)' }} 
            axisLine={false} 
            tickLine={false}
            interval="preserveStartEnd"
            minTickGap={20}
          />
          <YAxis 
            stroke="var(--color-text-muted)" 
            fontSize={10} 
            tick={{ fill: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }} 
            axisLine={false} 
            tickLine={false} 
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Background reference areas for CPCB bands (simplified for clarity) */}
          <ReferenceArea y1={0} y2={60} fill="var(--aqi-good-bg)" opacity={0.3} />
          <ReferenceArea y1={60} y2={90} fill="var(--aqi-moderate-bg)" opacity={0.3} />
          <ReferenceArea y1={90} y2={250} fill="var(--aqi-poor-bg)" opacity={0.3} />

          {/* Lines */}
          <Line
            type="monotone"
            dataKey="observedPm25"
            stroke="var(--color-observed)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: 'var(--color-observed)', stroke: 'var(--color-bg-base)' }}
            isAnimationActive={true}
            animationDuration={800}
          />
          <Line
            type="monotone"
            dataKey="forecastPm25"
            stroke="var(--color-modelled)"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            activeDot={{ r: 4, fill: 'var(--color-modelled)', stroke: 'var(--color-bg-base)' }}
            isAnimationActive={true}
            animationDuration={800}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
