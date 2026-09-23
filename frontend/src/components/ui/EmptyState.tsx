import React from 'react';
import { Activity } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title?: string;
  hint?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title = 'No data available',
  hint,
}) => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 'var(--space-3)',
      padding: 'var(--space-6)',
      height: '100%',
      textAlign: 'center',
    }}
  >
    <div
      style={{
        width: '40px',
        height: '40px',
        borderRadius: 'var(--radius-lg)',
        background: 'var(--color-bg-elevated)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-text-muted)',
      }}
      aria-hidden="true"
    >
      {icon ?? <Activity size={20} />}
    </div>
    <div>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', fontWeight: 500, marginBottom: '4px' }}>
        {title}
      </p>
      {hint && (
        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
          {hint}
        </p>
      )}
    </div>
  </div>
);
