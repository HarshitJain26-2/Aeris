import React from 'react';

interface RangeSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (val: number) => void;
  disabled?: boolean;
}

export const RangeSlider: React.FC<RangeSliderProps> = ({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  disabled = false,
}) => {
  const percent = ((value - min) / (max - min)) * 100;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <label
          style={{
            fontSize: 'var(--text-sm)',
            fontWeight: 500,
            color: disabled ? 'var(--color-text-muted)' : 'var(--color-text-primary)',
          }}
        >
          {label}
        </label>
        <span
          style={{
            fontSize: 'var(--text-sm)',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            color: disabled ? 'var(--color-text-muted)' : 'var(--color-teal)',
          }}
        >
          {value}%
        </span>
      </div>

      <div style={{ position: 'relative', height: '24px', display: 'flex', alignItems: 'center' }}>
        {/* Custom Track */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            height: '6px',
            borderRadius: '3px',
            background: 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: 0,
            width: `${percent}%`,
            height: '6px',
            borderRadius: '3px',
            background: disabled ? 'var(--color-text-muted)' : 'var(--color-teal)',
          }}
        />

        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          disabled={disabled}
          aria-label={label}
          style={{
            position: 'absolute',
            width: '100%',
            opacity: 0,
            cursor: disabled ? 'not-allowed' : 'pointer',
            height: '100%',
            margin: 0,
          }}
        />
        
        {/* Custom Thumb visual */}
        <div
          style={{
            position: 'absolute',
            left: `calc(${percent}% - 8px)`,
            width: '16px',
            height: '16px',
            borderRadius: '50%',
            background: disabled ? 'var(--color-text-muted)' : '#fff',
            boxShadow: 'var(--shadow-card)',
            border: disabled ? 'none' : '2px solid var(--color-teal)',
            pointerEvents: 'none',
          }}
        />
      </div>
    </div>
  );
};
