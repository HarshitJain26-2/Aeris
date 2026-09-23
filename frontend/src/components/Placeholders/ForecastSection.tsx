import React from 'react';
import { TrendingUp, Clock } from 'lucide-react';
import './Placeholders.css';

export const ForecastSection: React.FC = () => {
  return (
    <div className="placeholder-card">
      <div className="placeholder-header">
        <div className="placeholder-icon-wrapper">
          <TrendingUp size={18} className="placeholder-icon" />
        </div>
        <div>
          <h3 className="placeholder-title">Forecasting — Next Development Stage</h3>
          <p className="placeholder-description">
            Environmental projection models and temporal pollutant forecasts will be integrated in subsequent milestones.
          </p>
        </div>
      </div>
      <div className="placeholder-status-badge">
        <Clock size={14} />
        <span>Pending Integration</span>
      </div>
    </div>
  );
};
