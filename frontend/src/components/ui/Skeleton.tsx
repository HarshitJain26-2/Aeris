import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '1rem',
  borderRadius = 'var(--radius-md)',
  style,
}) => (
  <div
    aria-hidden="true"
    className="skeleton"
    style={{ width, height, borderRadius, flexShrink: 0, ...style }}
  />
);

interface SkeletonPanelProps {
  rows?: number;
  showHeader?: boolean;
}

export const SkeletonPanel: React.FC<SkeletonPanelProps> = ({
  rows = 3,
  showHeader = true,
}) => (
  <div style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
    {showHeader && (
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
        <Skeleton width="40%" height="0.875rem" />
        <Skeleton width="80px" height="1.5rem" borderRadius="var(--radius-full)" />
      </div>
    )}
    {Array.from({ length: rows }).map((_, i) => (
      <Skeleton key={i} height="2rem" style={{ opacity: 1 - i * 0.15 }} />
    ))}
  </div>
);
