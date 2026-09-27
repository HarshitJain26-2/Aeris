import React, { useState } from 'react';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { useAirQuality } from './hooks/useAirQuality';
import type { SelectedMapEntity } from './types/zone';

export const App: React.FC = () => {
  const { data } = useAirQuality();
  const [selectedEntity, setSelectedEntity] = useState<SelectedMapEntity | null>(null);

  const selectedName =
    selectedEntity?.type === 'zone'
      ? selectedEntity.zone.name
      : selectedEntity?.type === 'hotspot'
      ? selectedEntity.name
      : undefined;

  return (
    <AppShell lastUpdated={data?.timestamp} selectedZoneName={selectedName}>
      <DashboardPage selectedEntity={selectedEntity} onSelectEntity={setSelectedEntity} />
    </AppShell>
  );
};

export default App;
