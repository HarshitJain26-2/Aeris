import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger';
  size?: 'sm' | 'md';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  disabled,
  style,
  ...props
}) => {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
    fontFamily: 'var(--font-sans)',
    fontWeight: 500,
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.45 : 1,
    border: 'none',
    borderRadius: 'var(--radius-md)',
    transition: 'all var(--transition-base)',
    padding: size === 'sm' ? '6px 12px' : '9px 18px',
    fontSize: size === 'sm' ? 'var(--text-sm)' : 'var(--text-base)',
    ...(variant === 'primary' && {
      background: 'var(--color-accent)',
      color: '#fff',
      boxShadow: 'none',
    }),
    ...(variant === 'ghost' && {
      background: 'transparent',
      color: 'var(--color-text-secondary)',
      border: '1px solid var(--color-border)',
    }),
    ...(variant === 'danger' && {
      background: 'var(--color-critical-bg)',
      color: 'var(--color-critical)',
      border: '1px solid var(--color-critical)',
    }),
    ...style,
  };

  return (
    <button
      {...props}
      className={`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base ${props.className || ''}`}
      disabled={disabled || loading}
      aria-busy={loading}
      style={baseStyle}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          if (variant === 'primary') {
            (e.currentTarget as HTMLButtonElement).style.filter = 'brightness(1.1)';
            (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 4px 12px color-mix(in srgb, var(--color-accent) 20%, transparent)';
          } else if (variant === 'ghost') {
            (e.currentTarget as HTMLButtonElement).style.background = 'var(--color-bg-elevated)';
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-text-primary)';
          }
        }
        props.onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        if (variant === 'primary') {
          (e.currentTarget as HTMLButtonElement).style.filter = 'none';
          (e.currentTarget as HTMLButtonElement).style.boxShadow = 'none';
        } else if (variant === 'ghost') {
          (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
          (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-text-secondary)';
        }
        props.onMouseLeave?.(e);
      }}
      onMouseDown={(e) => {
        if (!disabled && !loading) {
          (e.currentTarget as HTMLButtonElement).style.transform = 'scale(0.97)';
        }
        props.onMouseDown?.(e);
      }}
      onMouseUp={(e) => {
        (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)';
        props.onMouseUp?.(e);
      }}
    >
      {loading ? (
        <>
          <span
            role="status"
            aria-label="Loading"
            style={{
              width: '14px',
              height: '14px',
              border: '2px solid rgba(255,255,255,0.3)',
              borderTopColor: '#fff',
              borderRadius: '50%',
              animation: 'spin 0.7s linear infinite',
              flexShrink: 0,
            }}
          />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </>
      ) : null}
      {children}
    </button>
  );
};
