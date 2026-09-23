import React from 'react';
import { TopBar } from './TopBar';
import { DemoRibbon } from './DemoRibbon';

interface AppShellProps {
  children: React.ReactNode;
  lastUpdated?: string;
}

export const AppShell: React.FC<AppShellProps> = ({ children, lastUpdated }) => {
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
      <DemoRibbon />
      <TopBar lastUpdated={lastUpdated} />
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
  );
};
