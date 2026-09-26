import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  accent?: 'observed' | 'modelled' | 'none';
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  accent = 'none',
  style,
}) => {
  const borderLeft =
    accent === 'observed'
      ? '2px solid var(--color-observed)'
      : accent === 'modelled'
      ? '2px dashed var(--color-modelled)'
      : undefined;

  return (
    <div
      className={`aeris-card ${className}`}
      style={{
        background: 'var(--color-bg-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        borderLeft,
        overflow: 'hidden',
        ...style,
      }}
    >
      {children}
    </div>
  );
};
