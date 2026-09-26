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
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
            fontWeight: 500,
            color: disabled ? 'var(--color-text-muted)' : '#0B1F3A',
          }}
        >
          {label}
        </label>
        <span
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: '16px',
            fontWeight: 700,
            color: disabled ? 'var(--color-text-muted)' : '#1769D2',
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
            background: '#DBEAFE',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: 0,
            width: `${percent}%`,
            height: '6px',
            borderRadius: '3px',
            background: disabled ? 'var(--color-text-muted)' : '#1769D2',
          }}
        />

        <input
          type="range"
          className="peer"
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
            background: '#FFFFFF',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            border: disabled ? 'none' : '2px solid #1769D2',
            pointerEvents: 'none',
          }}
          className="peer-focus-visible:outline-none peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-accent peer-focus-visible:ring-offset-bg-surface"
        />
      </div>
    </div>
  );
};
