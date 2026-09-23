import React from 'react';
import { Sliders, Clock } from 'lucide-react';
import './Placeholders.css';

export const ScenarioSection: React.FC = () => {
  return (
    <div className="placeholder-card">
      <div className="placeholder-header">
        <div className="placeholder-icon-wrapper">
          <Sliders size={18} className="placeholder-icon" />
        </div>
        <div>
          <h3 className="placeholder-title">Scenario Simulation — Next Development Stage</h3>
          <p className="placeholder-description">
            Urban policy interventions, emission scenario adjustments, and counterfactual models will be integrated in subsequent milestones.
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
