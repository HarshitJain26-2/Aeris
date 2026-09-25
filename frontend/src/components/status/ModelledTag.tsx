import React from 'react';
import { Cpu } from 'lucide-react';

interface ModelledTagProps {
  label?: string;
}

export const ModelledTag: React.FC<ModelledTagProps> = ({ label = 'Model estimate' }) => (
  <span
    role="status"
    aria-label="Data source: model estimate"
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      padding: '3px 8px',
      borderRadius: 'var(--radius-full)',
      background: 'transparent',
      border: '1px dashed #14508C',
      color: '#14508C',
      fontSize: 'var(--text-xs)',
      fontWeight: 600,
      letterSpacing: '0.04em',
      textTransform: 'uppercase',
      userSelect: 'none',
    }}
  >
    <Cpu size={11} aria-hidden="true" />
    {label}
  </span>
);
