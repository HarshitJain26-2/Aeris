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
          <div className="brand-icon-wrapper">
            <Globe size={14} color="#FFFFFF" />
          </div>
          <span className="brand-name">AERIS</span>
        </div>
      </div>

      <div className="sidebar-section-title">Navigation</div>
      <nav className="sidebar-nav">
        <button
          type="button"
          className={`nav-item ${activeTab === 'map' ? 'active' : ''}`}
          onClick={() => onTabChange('map')}
        >
          <Map size={16} />
          <span>Dashboard</span>
        </button>

        <button
          type="button"
          className={`nav-item ${activeTab === 'zones' ? 'active' : ''}`}
          onClick={() => onTabChange('zones')}
        >
          <Layers size={16} />
          <span>Map</span>
        </button>

        <button
          type="button"
          className={`nav-item ${activeTab === 'forecast' ? 'active' : ''}`}
          onClick={() => onTabChange('forecast')}
        >
          <TrendingUp size={16} />
          <span>Validate</span>
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
        Cleaner Cities, Healthier Tomorrow
      </div>
    </aside>
  );
};
