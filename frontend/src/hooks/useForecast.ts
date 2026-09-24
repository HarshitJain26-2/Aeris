import { useAsync } from './useAsync';
import { getForecast } from '../services/api';
export const useForecast = () => useAsync(getForecast);
