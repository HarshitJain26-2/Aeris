import { useState } from 'react';
import { Sidebar } from './components/Navigation/Sidebar';
import { MapLibreView } from './components/Map/MapLibreView';
import { ForecastSection } from './components/Placeholders/ForecastSection';
import { ScenarioSection } from './components/Placeholders/ScenarioSection';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<string>('map');

  return (
    <div className="aeris-shell">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="aeris-main">
        <header className="aeris-header">
          <div className="header-left">
            <h1 className="header-title">AERIS — Urban Environmental Intelligence & Digital Twin</h1>
            <span className="header-subtitle">Pune Urban Region • GIS Foundation Active</span>
          </div>
          <div className="header-right">
            <div className="system-badge">
              <span className="status-live-dot"></span>
              <span>Foundation M3</span>
            </div>
          </div>
        </header>

        <div className="aeris-content-scroll">
          <section className="map-section">
            <div className="section-header">
              <h2 className="section-title">Urban Spatial Twin — Pune Test Zones</h2>
              <span className="section-meta">6 Mock Zones Loaded via Local GeoJSON</span>
            </div>
            <div className="map-viewport">
              <MapLibreView />
            </div>
          </section>

          <div className="placeholders-grid">
            <ForecastSection />
            <ScenarioSection />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
