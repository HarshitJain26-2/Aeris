import React from 'react';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { useAirQuality } from './hooks/useAirQuality';

export const App: React.FC = () => {
  const { data } = useAirQuality();

  return (
    <AppShell lastUpdated={data?.timestamp}>
      <DashboardPage />
    </AppShell>
  );
};

export default App;
