import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  color = 'blue',
}) => {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    green: 'bg-green-50 text-green-600 border-green-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
    orange: 'bg-orange-50 text-orange-600 border-orange-100',
    red: 'bg-red-50 text-red-600 border-red-100',
  };

  const changeColorMap = {
    positive: 'text-green-600 bg-green-50',
    negative: 'text-red-600 bg-red-50',
    neutral: 'text-gray-600 bg-gray-50',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change && (
            <div className={`mt-2 text-xs font-medium px-2 py-1 rounded-full inline-flex items-center ${changeColorMap[changeType]}`}>
              {change}
            </div>
          )}
        </div>
        {icon && (
          <div className={`p-3 rounded-xl ${colorMap[color]}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

interface ProgressCardProps {
  title: string;
  value: number;
  max: number;
  label?: string;
  color?: string;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({
  title,
  value,
  max,
  label,
  color = 'blue',
}) => {
  const percentage = max > 0 ? (value / max) * 100 : 0;
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {label && <span className="text-sm text-gray-500">{label}</span>}
      </div>
      <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorClasses[color]}`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
      <div className="mt-2 flex items-center justify-between text-sm">
        <span className="text-gray-500">{value} / {max}</span>
        <span className="font-medium text-gray-700">{percentage.toFixed(0)}%</span>
      </div>
    </div>
  );
};

interface ListCardProps {
  title: string;
  items: Array<{
    id: string;
    title: string;
    subtitle?: string;
    status?: string;
    statusColor?: string;
    time?: string;
  }>;
  actionLabel?: string;
  onAction?: () => void;
}

export const ListCard: React.FC<ListCardProps> = ({
  title,
  items,
  actionLabel,
  onAction,
}) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {actionLabel && (
          <button onClick={onAction} className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All
          </button>
        )}
      </div>
      <div className="divide-y">
        {items.map((item) => (
          <div key={item.id} className="p-4 hover:bg-gray-50">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">{item.title}</h4>
                {item.subtitle && (
                  <p className="text-sm text-gray-500 mt-1">{item.subtitle}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {item.status && (
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    item.statusColor === 'green' ? 'bg-green-100 text-green-700' :
                    item.statusColor === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
                    item.statusColor === 'red' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {item.status}
                  </span>
                )}
                {item.time && (
                  <span className="text-xs text-gray-400">{item.time}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

interface ChartCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}

export const ChartCard: React.FC<ChartCardProps> = ({ title, subtitle, children, action }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="p-4 border-b flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
};

interface QuotaCardProps {
  used: number;
  total: number;
  label: string;
  unit?: string;
}

export const QuotaCard: React.FC<QuotaCardProps> = ({ used, total, label, unit = '' }) => {
  const percentage = total > 0 ? (used / total) * 100 : 0;
  const isWarning = percentage > 80;
  const isDanger = percentage > 95;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">{label}</h3>
        <span className={`text-sm font-medium ${
          isDanger ? 'text-red-600' : isWarning ? 'text-orange-600' : 'text-gray-600'
        }`}>
          {percentage.toFixed(0)}%
        </span>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isDanger ? 'bg-red-500' : isWarning ? 'bg-orange-500' : 'bg-blue-500'
          }`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-500">{used.toLocaleString()} {unit} used</span>
        <span className="text-gray-700 font-medium">{total.toLocaleString()} {unit} total</span>
      </div>
      {!isDanger && (
        <p className="mt-3 text-xs text-gray-500">
          {(total - used).toLocaleString()} {unit} remaining
        </p>
      )}
    </div>
  );
};

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'info' | 'pending';
  label: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const styles = {
    success: 'bg-green-100 text-green-700 border-green-200',
    warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    error: 'bg-red-100 text-red-700 border-red-200',
    info: 'bg-blue-100 text-blue-700 border-blue-200',
    pending: 'bg-gray-100 text-gray-700 border-gray-200',
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full border ${styles[status]}`}>
      {label}
    </span>
  );
};

interface ActionCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}

export const ActionCard: React.FC<ActionCardProps> = ({
  title,
  description,
  icon,
  onClick,
  disabled,
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full text-left p-6 bg-white rounded-xl shadow-sm border border-gray-100 
        hover:border-blue-200 hover:shadow-md transition-all ${
          disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
        }`}
    >
      <div className="flex items-start gap-4">
        <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">{icon}</div>
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-500 mt-1">{description}</p>
        </div>
      </div>
    </button>
  );
};

export default {
  StatCard,
  ProgressCard,
  ListCard,
  ChartCard,
  QuotaCard,
  StatusBadge,
  ActionCard,
};