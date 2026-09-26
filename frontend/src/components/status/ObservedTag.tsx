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
      borderRadius: 'var(--radius-md)',
      background: '#2E9E5B',
      border: 'none',
      color: '#FFFFFF',
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
