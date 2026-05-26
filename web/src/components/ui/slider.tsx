import * as React from 'react';
import { cn } from '@/lib/utils';

interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {
  value?: number[];
  onValueChange?: (value: number[]) => void;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, value = [0], onValueChange, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>, index: number) => {
      const newValue = [...value];
      newValue[index] = Number(e.target.value);
      onValueChange?.(newValue);
    };

    const percentage = ((value[0] - Number(props.min || 0)) / (Number(props.max || 100) - Number(props.min || 0))) * 100;

    return (
      <div className={cn('relative flex w-full items-center', className)}>
        <input
          ref={ref}
          type="range"
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          value={value[0]}
          onChange={(e) => handleChange(e, 0)}
          style={{
            background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`,
          }}
          {...props}
        />
      </div>
    );
  }
);
Slider.displayName = 'Slider';

export { Slider };