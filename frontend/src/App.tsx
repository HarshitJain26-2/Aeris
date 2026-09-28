import React, { useState } from 'react';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { useAirQuality } from './hooks/useAirQuality';
import type { SelectedMapEntity } from './types/zone';

export const App: React.FC = () => {
  const { data } = useAirQuality();
  const [selectedEntity, setSelectedEntity] = useState<SelectedMapEntity | null>(null);

  return (
    <AppShell lastUpdated={data?.timestamp}>
      <DashboardPage selectedEntity={selectedEntity} onSelectEntity={setSelectedEntity} />
    </AppShell>
  );
};

export default App;
