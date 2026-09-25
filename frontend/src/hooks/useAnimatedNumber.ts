import { useState, useEffect, useRef } from 'react';

const easeOutExpo = (t: number): number => {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
};

export const useAnimatedNumber = (targetValue: number, duration: number = 700): number => {
  const [displayValue, setDisplayValue] = useState(targetValue);
  const startValueRef = useRef(targetValue);
  const targetValueRef = useRef(targetValue);
  const requestRef = useRef<number>(0);

  useEffect(() => {
    if (targetValue === targetValueRef.current) {
      return;
    }
    
    startValueRef.current = displayValue;
    targetValueRef.current = targetValue;
    let startTime: number | null = null;

    const animate = (time: number) => {
      if (startTime === null) {
        startTime = time;
      }

      const elapsed = time - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutExpo(progress);

      const nextValue = startValueRef.current + (targetValue - startValueRef.current) * easedProgress;
      setDisplayValue(nextValue);

      if (progress < 1) {
        requestRef.current = requestAnimationFrame(animate);
      } else {
        setDisplayValue(targetValue);
      }
    };

    requestRef.current = requestAnimationFrame(animate);

    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetValue, duration]);

  return displayValue;
};
