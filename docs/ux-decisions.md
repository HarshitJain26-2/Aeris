# AERIS Frontend UX Decisions

This document captures the visual and interaction design principles applied in Round 1 for the AERIS Urban Environmental Digital Twin.

## 1. Visual Language: Environmental Intelligence

**Goal:** Create a premium, authoritative tool for urban operators.
**Constraint:** Avoid generic "AI SaaS" neon-blue/purple themes.

**Decisions:**
- **Warm Graphite Palette:** The base background is a warm graphite (`#0f0f0e`, `#1a1917`) instead of cold blue-black. This grounds the interface and feels more like physical infrastructure than digital ephemeral software.
- **Restrained Accent:** Primary interactive elements use a restrained teal (`#0d9488`). Teal is associated with environment and water, fitting the domain.
- **Minimal Glassmorphism:** Glass effects are used only on overlays (LayerToggle, MapLegend) where map context must be preserved beneath.

## 2. Core Differentiator: Observed vs Modelled

**Goal:** Clearly distinguish real sensor data from machine learning estimates.

**Decisions:**
- **OBSERVED:** Uses forest green (`#16a34a`), solid chart lines (`strokeWidth=2`), and solid map layers (`opacity: 0.8`). Labelled explicitly with a `● Observed` tag.
- **MODELLED / FORECAST:** Uses warm amber (`#d97706`), dashed chart lines (`strokeDasharray="5 4"`), and lower-opacity map layers. Labelled explicitly with a `◈ Model estimate` tag.
- **Disclaimer Banner:** A persistent `DemoRibbon` is added at the top during development to explicitly state that mock fixtures are active.

## 3. Map-First Layout

**Goal:** Ensure the Digital Twin feels geospatial and context-aware.

**Decisions:**
- **Hero Placement:** The map occupies the central flex-grow column.
- **No Stub Pages:** Unnecessary navigation links (e.g., placeholder Map/Validate pages) were removed to focus entirely on the core vertical slice on one dashboard.

## 4. Scenario Simulation (What-If) UX

**Goal:** Provide an interactive scenario tool without faking "AI processing".

**Decisions:**
- **Deterministic Calculation:** The frontend uses a real linear formula (elasticity-based) to compute the scenario instantly.
- **No Artificial Delay:** We do NOT manufacture a fake 400ms delay. The result appears instantly with a smooth CSS fade-in.
- **Transparency:** The mathematical formula `Δ = Baseline × (1 - reduction × 0.40 × 0.80)` is printed directly in the UI.

## 5. CPCB AQI Standardization

**Goal:** Use geographically appropriate standards.

**Decisions:**
- **Terminology:** Replaced "WHO bands" with "India National AQI / CPCB".
- **Colors:** The `AqiBadge` component strictly maps to the 6 CPCB bands (Good, Satisfactory, Moderate, Poor, Very Poor, Severe).
- **Scale:** Standardized 0-500+ scale on the MapLegend.
