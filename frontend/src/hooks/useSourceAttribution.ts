import { useAsync } from './useAsync';
import { getDriverAttribution } from '../services/api';
export const useSourceAttribution = () => useAsync(getDriverAttribution);
