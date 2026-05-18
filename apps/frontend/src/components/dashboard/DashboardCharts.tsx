import React from 'react';

interface LineChartProps {
  data: Array<{ label: string; value: number }>;
  height?: number;
  color?: string;
  showDots?: boolean;
}

export const LineChart: React.FC<LineChartProps> = ({
  data,
  height = 200,
  color = '#3b82f6',
  showDots = true,
}) => {
  if (!data.length) return null;

  const maxValue = Math.max(...data.map((d) => d.value));
  const minValue = Math.min(...data.map((d) => d.value));
  const range = maxValue - minValue || 1;

  const points = data.map((d, i) => ({
    x: (i / (data.length - 1)) * 100,
    y: 100 - ((d.value - minValue) / range) * 100,
    value: d.value,
    label: d.label,
  }));

  const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaPath = `${pathData} L 100 100 L 0 100 Z`;

  return (
    <svg viewBox="0 0 100 100" className="w-full" style={{ height }}>
      <defs>
        <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill="url(#lineGradient)" />
      <path d={pathData} fill="none" stroke={color} strokeWidth="2" />
      {showDots &&
        points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="2"
            fill={color}
            className="hover:r-3 transition-all"
          />
        ))}
    </svg>
  );
};

interface BarChartProps {
  data: Array<{ label: string; value: number; color?: string }>;
  height?: number;
  maxValue?: number;
}

export const BarChart: React.FC<BarChartProps> = ({ data, height = 200, maxValue }) => {
  const max = maxValue || Math.max(...data.map((d) => d.value)) || 1;

  return (
    <div className="flex items-end gap-2 h-full">
      {data.map((d, i) => {
        const percentage = (d.value / max) * 100;
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div
              className="w-full rounded-t transition-all duration-500"
              style={{
                height: `${percentage}%`,
                minHeight: d.value > 0 ? '4px' : '0',
                backgroundColor: d.color || '#3b82f6',
              }}
            />
            <span className="text-xs text-gray-500 truncate w-full text-center">{d.label}</span>
          </div>
        );
      })}
    </div>
  );
};

interface DonutChartProps {
  data: Array<{ label: string; value: number; color: string }>;
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerValue?: string | number;
}

export const DonutChart: React.FC<DonutChartProps> = ({
  data,
  size = 160,
  thickness = 24,
  centerLabel,
  centerValue,
}) => {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  let currentAngle = -90;

  const getArcPath = (startAngle: number, endAngle: number, radius: number) => {
    const start = (startAngle * Math.PI) / 180;
    const end = (endAngle * Math.PI) / 180;
    const x1 = 50 + radius * Math.cos(start);
    const y1 = 50 + radius * Math.sin(start);
    const x2 = 50 + radius * Math.cos(end);
    const y2 = 50 + radius * Math.sin(end);
    const large = endAngle - startAngle > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2}`;
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} viewBox="0 0 100 100">
        {data.map((d, i) => {
          const angle = (d.value / total) * 360;
          const startAngle = currentAngle;
          const endAngle = currentAngle + angle;
          currentAngle = endAngle;
          const radius = 40;
          return (
            <path
              key={i}
              d={getArcPath(startAngle, endAngle - 0.5, radius)}
              fill="none"
              stroke={d.color}
              strokeWidth={thickness}
              strokeLinecap="round"
            />
          );
        })}
      </svg>
      {(centerLabel || centerValue) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {centerValue && <span className="text-2xl font-bold text-gray-900">{centerValue}</span>}
          {centerLabel && <span className="text-xs text-gray-500">{centerLabel}</span>}
        </div>
      )}
    </div>
  );
};

interface PieChartProps {
  data: Array<{ label: string; value: number; color: string }>;
  size?: number;
}

export const PieChart: React.FC<PieChartProps> = ({ data, size = 160 }) => {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  let currentAngle = -90;

  const getArcPath = (startAngle: number, endAngle: number) => {
    const start = (startAngle * Math.PI) / 180;
    const end = (endAngle * Math.PI) / 180;
    const radius = 50;
    const x1 = 50 + radius * Math.cos(start);
    const y1 = 50 + radius * Math.sin(start);
    const x2 = 50 + radius * Math.cos(end);
    const y2 = 50 + radius * Math.sin(end);
    const large = endAngle - startAngle > 180 ? 1 : 0;
    return `M 50 50 L ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2} Z`;
  };

  return (
    <div className="flex items-center gap-6">
      <svg width={size} height={size} viewBox="0 0 100 100">
        {data.map((d, i) => {
          const angle = (d.value / total) * 360;
          const startAngle = currentAngle;
          const endAngle = currentAngle + angle;
          currentAngle = endAngle;
          return <path key={i} d={getArcPath(startAngle, endAngle - 0.5)} fill={d.color} />;
        })}
      </svg>
      <div className="space-y-2">
        {data.map((d, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.color }} />
            <span className="text-sm text-gray-600">{d.label}</span>
            <span className="text-sm font-medium text-gray-900">
              {((d.value / total) * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

interface ProgressRingProps {
  value: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  backgroundColor?: string;
  label?: string;
}

export const ProgressRing: React.FC<ProgressRingProps> = ({
  value,
  size = 120,
  strokeWidth = 8,
  color = '#3b82f6',
  backgroundColor = '#e5e7eb',
  label,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, value));
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={backgroundColor}
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-gray-900">{progress.toFixed(0)}%</span>
        {label && <span className="text-xs text-gray-500">{label}</span>}
      </div>
    </div>
  );
};

interface ActivityTimelineProps {
  activities: Array<{
    id: string;
    type: 'upload' | 'process' | 'complete' | 'error';
    title: string;
    description?: string;
    time: string;
    icon?: React.ReactNode;
  }>;
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ activities }) => {
  const iconMap = {
    upload: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    ),
    process: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    complete: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    error: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  };

  const colorMap = {
    upload: 'text-blue-600 bg-blue-100',
    process: 'text-yellow-600 bg-yellow-100',
    complete: 'text-green-600 bg-green-100',
    error: 'text-red-600 bg-red-100',
  };

  return (
    <div className="space-y-4">
      {activities.map((activity, idx) => (
        <div key={activity.id} className="flex items-start gap-3">
          <div className={`p-2 rounded-full ${colorMap[activity.type]}`}>
            {activity.icon || iconMap[activity.type]}
          </div>
          <div className="flex-1 pt-1">
            <p className="font-medium text-gray-900">{activity.title}</p>
            {activity.description && (
              <p className="text-sm text-gray-500 mt-1">{activity.description}</p>
            )}
            <p className="text-xs text-gray-400 mt-1">{activity.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default {
  LineChart,
  BarChart,
  DonutChart,
  PieChart,
  ProgressRing,
  ActivityTimeline,
};