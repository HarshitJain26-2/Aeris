import React from 'react';
import { Eye } from 'lucide-react';

interface ObservedTagProps {
  label?: string;
}

export const ObservedTag: React.FC<ObservedTagProps> = ({ label = 'Observed' }) => (
  <span
    role="status"
    aria-label="Data source: observed sensor reading"
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      padding: '3px 8px 3px 6px',
      borderRadius: 'var(--radius-sm)',
      background: 'var(--color-observed-bg)',
      border: '1px solid rgba(22,163,74,0.1)',
      borderLeft: '3px solid var(--color-observed)',
      color: 'var(--color-observed)',
      fontSize: 'var(--text-xs)',
      fontWeight: 600,
      letterSpacing: '0.04em',
      textTransform: 'uppercase',
      userSelect: 'none',
    }}
  >
    <Eye size={11} aria-hidden="true" />
    {label}
  </span>
);
