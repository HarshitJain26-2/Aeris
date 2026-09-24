import { useAsync } from './useAsync';
import { getHotspots } from '../services/api';
export const useHotspots = () => useAsync(getHotspots);
