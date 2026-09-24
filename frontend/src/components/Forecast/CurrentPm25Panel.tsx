import React from 'react';
import { Activity, Radio } from 'lucide-react';
import './ForecastSection.css';

interface CurrentPm25PanelProps {
  zoneName: string;
  currentPm25: number | null | undefined;
  unit?: string;
  lastUpdated?: string;
}

export const CurrentPm25Panel: React.FC<CurrentPm25PanelProps> = ({
  zoneName,
  currentPm25,
  unit = 'µg/m³',
  lastUpdated,
}) => {
  const hasObservation = typeof currentPm25 === 'number' && !Number.isNaN(currentPm25);

  return (
    <div className="current-condition-card">
      <div className="card-top-bar">
        <div className="card-title-group">
          <div className="card-icon-bubble">
            <Activity size={16} className="card-icon" />
          </div>
          <div>
            <h4 className="card-title">Current Air Quality</h4>
            <span className="card-zone-tag">{zoneName}</span>
          </div>
        </div>

        {/* Consistent OBSERVED indicator: solid visual representation */}
        <div className="observed-badge-solid" title="Observed ground sensor measurement">
          <span className="dot-solid" />
          <span className="badge-text">OBSERVED</span>
        </div>
      </div>

      <div className="current-reading-area">
        {hasObservation ? (
          <div className="reading-value-box">
            <div className="value-row">
              <span className="reading-number">{currentPm25.toFixed(1)}</span>
              <span className="reading-unit">{unit}</span>
            </div>
            <div className="reading-meta">
              <span className="reading-pollutant">PM2.5 Particulate Matter</span>
              {lastUpdated && (
                <span className="reading-timestamp">Observed at {new Date(lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              )}
            </div>
          </div>
        ) : (
          <div className="no-observation-box">
            <Radio size={18} className="no-obs-icon" />
            <div className="no-obs-content">
              <p className="no-obs-title">No observation data available</p>
              <p className="no-obs-subtitle">Awaiting sensor station telemetry stream for this zone</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
