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
      ? '2px solid var(--color-modelled)'
      : undefined;

  return (
    <div
      className={className}
      style={{
        background: 'var(--color-bg-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        borderLeft,
        boxShadow: 'var(--shadow-card)',
        overflow: 'hidden',
        transition: 'box-shadow var(--transition-base), border-color var(--transition-base)',
        ...style,
      }}
    >
      {children}
    </div>
  );
};
