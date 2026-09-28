import React from 'react';
import { X, Award, CheckCircle, TrendingDown, AlertTriangle, ShieldCheck, Clock } from 'lucide-react';
import { useModelValidation } from '../../hooks/useModelValidation';
import { Spinner } from '../ui/Spinner';
import { ErrorState } from '../ui/ErrorState';

interface ValidationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ValidationModal: React.FC<ValidationModalProps> = ({ isOpen, onClose }) => {
  const { data, loading, error, refetch } = useModelValidation();

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{
        background: 'rgba(11, 31, 58, 0.65)',
        backdropFilter: 'blur(4px)',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="w-full max-w-4xl max-h-[90vh] bg-white rounded-2xl shadow-2xl border border-border flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="validation-title"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-bg-surface shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-teal/15 text-teal flex items-center justify-center">
              <Award size={20} />
            </div>
            <div>
              <h2 id="validation-title" className="text-lg font-bold text-text-primary m-0 flex items-center gap-2">
                Historical Validation Evidence
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-mono font-medium">
                  Temporal Holdout (23h)
                </span>
              </h2>
              <p className="text-xs text-text-secondary m-0 mt-0.5">
                Benchmark evaluation of 1-hour-ahead XGBoost model vs. Persistence Baseline
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-slate-100 transition-colors"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 flex flex-col gap-6">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3">
              <Spinner size={32} color="var(--color-accent)" />
              <p className="text-sm font-medium text-text-secondary">Loading validation benchmarks...</p>
            </div>
          ) : error || !data ? (
            <div className="py-12">
              <ErrorState title="Failed to load validation benchmarks" onRetry={refetch} />
            </div>
          ) : (
            <>
              {/* Provenance & Methodology Notice */}
              <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 flex items-start gap-3">
                <AlertTriangle size={18} className="text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs text-amber-900 leading-relaxed">
                  <span className="font-semibold text-amber-950">Scientific & Provenance Disclosure: </span>
                  {data.disclaimer}
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* MAE */}
                <div className="p-4 rounded-xl border border-border bg-slate-50/60 flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text-secondary uppercase">XGBoost MAE</span>
                    <CheckCircle size={14} className="text-teal" />
                  </div>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-2xl font-bold font-mono text-text-primary">{data.mae}</span>
                    <span className="text-xs text-text-secondary">µg/m³</span>
                  </div>
                  <span className="text-xs text-text-muted mt-1">
                    vs Persistence: <span className="font-mono">{data.persistence_mae}</span>
                  </span>
                  <div className="mt-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded flex items-center gap-1 w-fit">
                    <TrendingDown size={12} />
                    {data.mae_improvement_pct}% Error Reduction
                  </div>
                </div>

                {/* RMSE */}
                <div className="p-4 rounded-xl border border-border bg-slate-50/60 flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text-secondary uppercase">XGBoost RMSE</span>
                    <CheckCircle size={14} className="text-teal" />
                  </div>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-2xl font-bold font-mono text-text-primary">{data.rmse}</span>
                    <span className="text-xs text-text-secondary">µg/m³</span>
                  </div>
                  <span className="text-xs text-text-muted mt-1">
                    vs Persistence: <span className="font-mono">{data.persistence_rmse}</span>
                  </span>
                  <div className="mt-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded flex items-center gap-1 w-fit">
                    <TrendingDown size={12} />
                    {data.rmse_improvement_pct}% Error Reduction
                  </div>
                </div>

                {/* R2 */}
                <div className="p-4 rounded-xl border border-border bg-slate-50/60 flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text-secondary uppercase">R² Fit</span>
                    <ShieldCheck size={14} className="text-blue-600" />
                  </div>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-2xl font-bold font-mono text-text-primary">{data.r2}</span>
                  </div>
                  <span className="text-xs text-text-muted mt-1">Explained Variance</span>
                  <div className="mt-2 text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded flex items-center gap-1 w-fit">
                    Strong Correlation
                  </div>
                </div>

                {/* Horizon & Split */}
                <div className="p-4 rounded-xl border border-border bg-slate-50/60 flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text-secondary uppercase">Horizon & Split</span>
                    <Clock size={14} className="text-indigo-600" />
                  </div>
                  <div className="text-sm font-bold text-text-primary mt-1">
                    {data.forecast_horizon}
                  </div>
                  <span className="text-xs text-text-muted mt-1">
                    Train: {data.training_rows}h • Test: {data.validation_rows}h
                  </span>
                  <div className="mt-2 text-xs font-medium text-slate-700 bg-slate-200/80 px-2 py-0.5 rounded w-fit">
                    {data.feature_count} Input Features
                  </div>
                </div>
              </div>

              {/* Holdout Observations vs Predictions Table */}
              {data.holdout_predictions && data.holdout_predictions.length > 0 && (
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-bold text-text-primary m-0 uppercase tracking-wide">
                      Temporal Holdout Sample (Unseen Test Hours)
                    </h3>
                    <span className="text-xs text-text-muted">
                      Target: CAMS Modeled PM2.5 • Timestamp: Asia/Kolkata
                    </span>
                  </div>

                  <div className="border border-border rounded-xl overflow-hidden shadow-sm">
                    <div className="max-h-60 overflow-y-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-100/90 text-text-secondary sticky top-0 border-b border-border font-medium">
                          <tr>
                            <th className="py-2.5 px-3">Hour (IST)</th>
                            <th className="py-2.5 px-3 text-right">Actual CAMS PM2.5</th>
                            <th className="py-2.5 px-3 text-right">XGBoost Forecast</th>
                            <th className="py-2.5 px-3 text-right">Persistence Baseline</th>
                            <th className="py-2.5 px-3 text-right">XGBoost Error</th>
                            <th className="py-2.5 px-3 text-right">Persistence Error</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border font-mono">
                          {data.holdout_predictions.slice(0, 10).map((row, idx) => {
                            const timeStr = row.timestamp.replace(':00+05:30', '').replace('2023-01-18 ', '');
                            const isXgbBetter = Math.abs(row.xgb_error) <= Math.abs(row.persistence_error);
                            return (
                              <tr key={idx} className="hover:bg-slate-50 transition-colors">
                                <td className="py-2 px-3 text-text-secondary font-sans">{timeStr}:00</td>
                                <td className="py-2 px-3 text-right text-text-primary font-semibold">{row.actual_pm25} µg/m³</td>
                                <td className="py-2 px-3 text-right text-teal font-semibold">{row.xgb_prediction} µg/m³</td>
                                <td className="py-2 px-3 text-right text-text-muted">{row.persistence_prediction} µg/m³</td>
                                <td className={`py-2 px-3 text-right font-semibold ${isXgbBetter ? 'text-emerald-700' : 'text-amber-700'}`}>
                                  {row.xgb_error > 0 ? `+${row.xgb_error}` : row.xgb_error}
                                </td>
                                <td className="py-2 px-3 text-right text-text-muted">
                                  {row.persistence_error > 0 ? `+${row.persistence_error}` : row.persistence_error}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <p className="text-[11px] text-text-muted m-0 italic">
                    Showing first 10 of {data.holdout_predictions.length} chronological validation test hours from Jan 18, 2023.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border bg-slate-50 flex items-center justify-between shrink-0">
          <span className="text-xs text-text-muted font-mono">
            Model Artifact: ml/models/xgb_pm25_forecaster.json
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-text-primary text-white hover:bg-slate-800 transition-colors"
          >
            Close Evidence View
          </button>
        </div>
      </div>
    </div>
  );
};
