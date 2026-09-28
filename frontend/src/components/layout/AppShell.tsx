import React from 'react';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
  lastUpdated?: string;
  selectedZoneName?: string;
  onOpenValidation?: () => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  lastUpdated,
  selectedZoneName,
  onOpenValidation,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        background: 'var(--color-bg-base)',
      }}
    >
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar onOpenValidation={onOpenValidation} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <TopBar
            lastUpdated={lastUpdated}
            selectedZoneName={selectedZoneName}
            onOpenValidation={onOpenValidation}
          />
          <main
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};
