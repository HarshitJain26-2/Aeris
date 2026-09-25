import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Data unavailable',
  message = 'An error occurred. Please try again.',
  onRetry,
}) => (
  <div
    role="alert"
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
        background: 'var(--color-critical-bg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <AlertTriangle size={20} color="var(--color-critical)" aria-hidden="true" />
    </div>
    <div>
      <p style={{ color: 'var(--color-text-primary)', fontWeight: 500, fontSize: 'var(--text-sm)', marginBottom: '4px' }}>
        {title}
      </p>
      <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
        {message}
      </p>
    </div>
    {onRetry && (
      <Button variant="ghost" size="sm" onClick={onRetry} aria-label="Retry">
        <RefreshCw size={13} aria-hidden="true" />
        Retry
      </Button>
    )}
  </div>
);
