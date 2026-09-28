import React, { useState } from 'react';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { ValidationModal } from './components/panels/ValidationModal';
import { useAirQuality } from './hooks/useAirQuality';
import type { SelectedMapEntity } from './types/zone';

export const App: React.FC = () => {
  const { data } = useAirQuality();
  const [selectedEntity, setSelectedEntity] = useState<SelectedMapEntity | null>(null);
  const [isValidationOpen, setIsValidationOpen] = useState(false);

  const selectedName =
    selectedEntity?.type === 'zone'
      ? selectedEntity.zone.name
      : selectedEntity?.type === 'hotspot'
      ? selectedEntity.name
      : undefined;

  return (
    <>
      <AppShell
        lastUpdated={data?.timestamp}
        selectedZoneName={selectedName}
        onOpenValidation={() => setIsValidationOpen(true)}
      >
        <DashboardPage selectedEntity={selectedEntity} onSelectEntity={setSelectedEntity} />
      </AppShell>
      <ValidationModal
        isOpen={isValidationOpen}
        onClose={() => setIsValidationOpen(false)}
      />
    </>
  );
};

export default App;
