export interface PredictionPoint {
  timestamp: string;
  actual_pm25: number;
  xgb_prediction: number;
  persistence_prediction: number;
  xgb_error: number;
  persistence_error: number;
}

export interface ModelValidationEvidence {
  model: string;
  target: string;
  forecast_horizon: string;
  validation_type: string;
  target_source: string;
  target_source_type: string;
  validation_rows: number;
  training_rows: number;
  feature_count: number;
  mae: number;
  rmse: number;
  r2: number;
  persistence_mae: number;
  persistence_rmse: number;
  mae_improvement: number;
  rmse_improvement: number;
  mae_improvement_pct: number;
  rmse_improvement_pct: number;
  beats_persistence_mae: boolean;
  beats_persistence_rmse: boolean;
  disclaimer: string;
  holdout_predictions?: PredictionPoint[];
}
