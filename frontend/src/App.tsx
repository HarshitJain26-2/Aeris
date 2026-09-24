import { useState } from 'react';
import { Sidebar } from './components/Navigation/Sidebar';
import { MapLibreView } from './components/Map/MapLibreView';
import { ForecastSection } from './components/Forecast/ForecastSection';
import { ScenarioSection } from './components/Placeholders/ScenarioSection';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<string>('map');
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);

  return (
    <div className="aeris-shell">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="aeris-main">
        <header className="aeris-header">
          <div className="header-left">
            <h1 className="header-title">AERIS — Urban Environmental Intelligence & Digital Twin</h1>
            <span className="header-subtitle">
              Pune Urban Region • GIS Foundation & 24h Environmental Forecasting
            </span>
          </div>
          <div className="header-right">
            <div className="system-badge">
              <span className="status-live-dot"></span>
              <span>Forecast M3 Active</span>
            </div>
          </div>
        </header>

        <div className="aeris-content-scroll">
          <section className="map-section">
            <div className="section-header">
              <h2 className="section-title">Urban Spatial Twin — Pune Test Zones</h2>
              <span className="section-meta">
                {selectedZoneId
                  ? `Active Zone: ${selectedZoneId.toUpperCase()} • Interactive Selection Enabled`
                  : '6 Mock Zones Loaded via Local GeoJSON • Click a zone to select'}
              </span>
            </div>
            <div className="map-viewport">
              <MapLibreView
                selectedZoneId={selectedZoneId}
                onSelectZone={setSelectedZoneId}
              />
            </div>
          </section>

          <div className="placeholders-grid">
            <ForecastSection
              selectedZoneId={selectedZoneId}
              onSelectZone={setSelectedZoneId}
            />
            <ScenarioSection />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
