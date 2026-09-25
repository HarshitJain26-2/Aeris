import { useAsync } from './useAsync';
import { getZones } from '../services/api';

export const useZones = () => useAsync(getZones);
