import { useAsync } from './useAsync';
import { getCurrentAirQuality } from '../services/api';
export const useAirQuality = () => useAsync(getCurrentAirQuality);
