import { useAsync } from './useAsync';
import { getModelValidation } from '../services/api';
import type { ModelValidationEvidence } from '../types/validation';

export function useModelValidation() {
  return useAsync<ModelValidationEvidence>(getModelValidation);
}
