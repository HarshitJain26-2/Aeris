import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import type { ForecastPoint } from '../../types/forecast';
import { BarChart3 } from 'lucide-react';
import './ForecastSection.css';

interface ActualVsPredictedChartProps {
  forecast?: ForecastPoint[] | null;
  unit?: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number | null | undefined;
    color: string;
    dataKey: string;
  }>;
  label?: string;
  unit: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, unit }) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  return (
    <div className="forecast-chart-tooltip">
      <div className="tooltip-header">{label}</div>
      <div className="tooltip-list">
        {payload.map((entry) => {
          const isActual = entry.dataKey === 'actual';
          const valueDisplay =
            typeof entry.value === 'number'
              ? `${entry.value.toFixed(1)} ${unit}`
              : 'No observation';

          return (
            <div key={entry.dataKey} className="tooltip-row">
              <div className="tooltip-row-label">
                {isActual ? (
                  <span className="tooltip-indicator-solid" />
                ) : (
                  <span className="tooltip-indicator-dashed" />
                )}
                <span>{entry.name}:</span>
              </div>
              <span className="tooltip-row-value">{valueDisplay}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const ActualVsPredictedChart: React.FC<ActualVsPredictedChartProps> = ({
  forecast,
  unit = 'µg/m³',
}) => {
  // Empty state check: do not fabricate numbers if no data is present
  const hasData = Array.isArray(forecast) && forecast.length > 0;

  if (!hasData) {
    return (
      <div className="chart-empty-container">
        <div className="chart-empty-icon-wrap">
          <BarChart3 size={24} className="chart-empty-icon" />
        </div>
        <p className="chart-empty-message">No forecast data available for this zone.</p>
        <span className="chart-empty-sub">
          Historical validation and future 24h projections will render once backend forecast points are provided.
        </span>
      </div>
    );
  }

  return (
    <div className="chart-wrapper">
      <div className="chart-legend-custom">
        <div className="legend-item">
          <span className="legend-symbol-solid" />
          <span className="legend-label">Actual (Observed)</span>
          <span className="legend-type-solid">SOLID</span>
        </div>
        <div className="legend-item">
          <span className="legend-symbol-dashed" />
          <span className="legend-label">Predicted (Modeled)</span>
          <span className="legend-type-dashed">DASHED</span>
        </div>
      </div>

      <div className="chart-canvas-container">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={forecast} margin={{ top: 10, right: 12, left: -10, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="timestamp"
              stroke="#94a3b8"
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={{ stroke: '#cbd5e1' }}
            />
            <YAxis
              stroke="#94a3b8"
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              unit={` ${unit}`}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip unit={unit} />} />
            {/* Hidden recharts default legend since we render an accessible custom header legend */}
            <Legend wrapperStyle={{ display: 'none' }} />

            {/* OBSERVED: Solid line */}
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual"
              stroke="#0284c7"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#ffffff', stroke: '#0284c7', strokeWidth: 2 }}
              activeDot={{ r: 5, fill: '#0284c7' }}
              connectNulls
              isAnimationActive={false}
            />

            {/* MODELED: Dashed line */}
            <Line
              type="monotone"
              dataKey="predicted"
              name="Predicted"
              stroke="#6366f1"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 2.5, fill: '#ffffff', stroke: '#6366f1', strokeWidth: 1.5 }}
              activeDot={{ r: 5, fill: '#6366f1' }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
