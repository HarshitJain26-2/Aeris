# AERIS Frontend Component Specification

This document details the core React components built for the AERIS Round 1 frontend.

## 1. UI Primitives (`src/components/ui/`)

### `AqiBadge`
Displays an AQI value with its corresponding India CPCB colour band.
- **Props**: `aqi: number`, `band?: CpcbBand`, `size?: 'sm' | 'md' | 'lg'`, `showPulse?: boolean`
- **Accessibility**: Uses `role="status"` and `aria-label` to announce the value and band to screen readers.

### `RangeSlider`
Custom range input for scenario parameters.
- **Props**: `label: string`, `value: number`, `min: number`, `max: number`, `onChange: (val: number) => void`, `disabled?: boolean`

### `Card`
Base container for dashboard panels.
- **Props**: `accent?: 'observed' | 'modelled' | 'none'` (adds left-border highlighting).

## 2. Layout (`src/components/layout/`)

### `AppShell`
Main layout wrapper.
- **Features**: Contains the `TopBar`, the `DemoRibbon` (critical for Round 1 to show mock status), and the main content area.

## 3. Data Visualization (`src/components/charts/`)

### `ForecastChart`
Recharts `ComposedChart` showing 24h PM2.5.
- **Features**: Solid line for past 6h (`observed`), dashed line for future 18h (`forecast`). CPCB background reference areas.

### `DriverDonut`
Recharts `PieChart` showing model-estimated driver attributions.
- **Features**: Custom hover tooltip. Uses `var(--color-teal)` and `var(--color-modelled)` tokens.

### `ScenarioCompare`
Recharts `BarChart` comparing Baseline vs Modelled PM2.5.
- **Features**: Visually links Baseline to the `observed` accent and Modelled to the `modelled` accent.

## 4. Map (`src/components/map/`)

### `HotspotMap`
MapLibre GL JS wrapper.
- **Features**: Loads CARTO dark matter tiles (no API key required). Renders a `heatmap` layer bound to `intensity` and a `circle` layer for click interactions.

## 5. Domain Panels (`src/components/panels/`)

Each panel is responsible for fetching its own data via a hook (e.g., `useAirQuality`) and handling Loading (`SkeletonPanel`), Error (`ErrorState`), and Success states.

- **ObservedPanel**: Top-left. Shows current sensor data.
- **ForecastPanel**: Middle-left. Shows PM2.5 time series.
- **DriverPanel**: Bottom-left. Shows source apportionment.
- **ScenarioPanel**: Right-side. Interactive what-if simulation tool.
