import React from 'react';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine
} from 'recharts';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import type { ForecastPoint } from '../../types/forecast';

interface ForecastChartProps {
  data: ForecastPoint[];
  loading?: boolean;
  error?: boolean;
  onRetry?: () => void;
}

interface TooltipPayloadItem {
  payload: {
    time: string;
    pm25: number;
    isForecast: boolean;
    observedPm25: number | null;
    forecastPm25: number | null;
    pm25Lower?: number;
    pm25Upper?: number;
  };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload;
    return (
      <div style={{
        background: 'var(--color-bg-elevated)',
        border: '1px solid var(--color-border)',
        padding: '8px 12px',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-pop)',
        fontFamily: 'var(--font-sans)',
        fontSize: '12px'
      }}>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '4px' }}>{label}</p>
        <p style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>
          {dataPoint.pm25} <span style={{ color: 'var(--color-text-muted)', fontWeight: 400 }}>µg/m³</span>
        </p>
        {dataPoint.pm25Lower != null && dataPoint.pm25Upper != null && (
          <p style={{ color: 'var(--color-text-muted)', fontSize: '11px', marginTop: '2px' }}>
            90% CI: {dataPoint.pm25Lower} – {dataPoint.pm25Upper} µg/m³
          </p>
        )}
        <p style={{ color: dataPoint.isForecast ? 'var(--color-modelled)' : 'var(--color-observed)', marginTop: '3px', fontWeight: 600, fontSize: '11px' }}>
          {dataPoint.isForecast ? 'Model Estimate (1h Horizon)' : 'Observed Telemetry'}
        </p>
      </div>
    );
  }
  return null;
};

export const ForecastChart: React.FC<ForecastChartProps> = ({ data, loading, error, onRetry }) => {
  if (error) {
    return (
      <div style={{ width: '100%', height: '200px' }}>
        <ErrorState title="Forecast service unavailable" onRetry={onRetry} />
      </div>
    );
  }
  if (loading) {
    return (
      <div style={{ width: '100%', height: '200px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', padding: '10px 0 20px' }}>
        {[40, 60, 45, 70, 55, 80, 65, 90, 50, 75].map((h, i) => (
          <Skeleton key={i} width="8%" height={`${h}%`} style={{ opacity: 0.4 }} />
        ))}
      </div>
    );
  }
  if (!data || data.length === 0) return null;

  // Format data for Recharts
  const chartData = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    pm25: d.pm25,
    isForecast: d.type === 'forecast',
    pm25Lower: d.pm25Lower,
    pm25Upper: d.pm25Upper,
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

  const showDots = chartData.length <= 4;

  return (
    <div style={{ width: '100%', height: '200px', minWidth: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke="var(--color-text-muted)" 
            fontSize={12} 
            tickMargin={8} 
            tick={{ fill: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }} 
            axisLine={false} 
            tickLine={false}
            interval="preserveStartEnd"
            minTickGap={20}
          />
          <YAxis 
            stroke="var(--color-text-muted)" 
            fontSize={12} 
            tick={{ fill: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }} 
            axisLine={false} 
            tickLine={false} 
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Background reference areas for CPCB bands */}
          <ReferenceArea y1={0} y2={60} fill="var(--aqi-good-bg)" />
          <ReferenceArea y1={60} y2={90} fill="var(--aqi-moderate-bg)" />
          <ReferenceArea y1={90} y2={250} fill="var(--aqi-poor-bg)" />

          <ReferenceLine 
            y={60} 
            stroke="var(--color-border)" 
            strokeDasharray="3 3" 
            label={{ value: 'Limit', position: 'insideTopLeft', fill: 'var(--color-text-muted)', fontSize: 11, fontFamily: 'var(--font-sans)' }} 
          />

          {/* Lines */}
          <Area
            type="monotone"
            dataKey="observedPm25"
            stroke="var(--color-observed)"
            fill="var(--color-observed-bg)"
            strokeWidth={2}
            dot={showDots ? { r: 4, fill: 'var(--color-observed)' } : false}
            activeDot={{ r: 5, fill: 'var(--color-observed)', stroke: 'var(--color-bg-base)' }}
            isAnimationActive={true}
            animationDuration={800}
          />
          <Line
            type="monotone"
            dataKey="forecastPm25"
            stroke="var(--color-modelled)"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={showDots ? { r: 5, fill: 'var(--color-modelled)' } : false}
            activeDot={{ r: 6, fill: 'var(--color-modelled)', stroke: 'var(--color-bg-base)' }}
            isAnimationActive={true}
            animationDuration={800}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
