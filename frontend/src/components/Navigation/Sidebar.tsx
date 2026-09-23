import React from 'react';
import { Map, Layers, TrendingUp, Sliders, Globe } from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <aside className="aeris-sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">
          <Globe size={20} className="brand-icon" />
          <span className="brand-name">AERIS</span>
        </div>
        <div className="brand-subtitle">Urban Digital Twin</div>
      </div>

      <div className="sidebar-section-title">Navigation</div>
      <nav className="sidebar-nav">
        <button
          type="button"
          className={`nav-item ${activeTab === 'map' ? 'active' : ''}`}
          onClick={() => onTabChange('map')}
        >
          <Map size={16} />
          <span>GIS Map View</span>
        </button>

        <button
          type="button"
          className={`nav-item ${activeTab === 'zones' ? 'active' : ''}`}
          onClick={() => onTabChange('zones')}
        >
          <Layers size={16} />
          <span>Urban Zones (6)</span>
        </button>

        <button
          type="button"
          className={`nav-item ${activeTab === 'forecast' ? 'active' : ''}`}
          onClick={() => onTabChange('forecast')}
        >
          <TrendingUp size={16} />
          <span>Forecasting</span>
          <span className="nav-tag">Next</span>
        </button>

        <button
          type="button"
          className={`nav-item ${activeTab === 'scenarios' ? 'active' : ''}`}
          onClick={() => onTabChange('scenarios')}
        >
          <Sliders size={16} />
          <span>Scenarios</span>
          <span className="nav-tag">Next</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status-box">
          <div className="status-header">
            <span className="system-indicator"></span>
            <span className="system-title">Region: Pune, MH</span>
          </div>
          <div className="system-desc">M3 Foundation Active</div>
        </div>
      </div>
    </aside>
  );
};
