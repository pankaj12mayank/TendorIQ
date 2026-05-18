import React, { useState, useEffect } from 'react';
import { AlertTriangle, AlertCircle, CheckCircle, Info, X, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';

interface RiskScoreGaugeProps {
  score: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export const RiskScoreGauge: React.FC<RiskScoreGaugeProps> = ({ score, severity }) => {
  const getColor = () => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const getLabel = () => {
    switch (severity) {
      case 'critical': return 'Critical Risk';
      case 'high': return 'High Risk';
      case 'medium': return 'Medium Risk';
      case 'low': return 'Low Risk';
      default: return 'Unknown';
    }
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-48">
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="96"
            cy="96"
            r="80"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="12"
          />
          <circle
            cx="96"
            cy="96"
            r="80"
            fill="none"
            stroke={getColor()}
            strokeWidth="12"
            strokeDasharray={`${(score / 100) * 502} 502`}
            strokeLinecap="round"
            className="transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold" style={{ color: getColor() }}>{Math.round(score)}</span>
          <span className="text-sm text-gray-500">/ 100</span>
        </div>
      </div>
      <div className="mt-4 px-4 py-2 rounded-full" style={{ backgroundColor: `${getColor()}20`, color: getColor() }}>
        {getLabel()}
      </div>
    </div>
  );
};

interface RiskCardProps {
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  score: number;
  recommendations?: string[];
  expanded?: boolean;
}

export const RiskCard: React.FC<RiskCardProps> = ({ title, severity, description, score, recommendations = [], expanded: initialExpanded = false }) => {
  const [expanded, setExpanded] = useState(initialExpanded);

  const getSeverityIcon = () => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-6 h-6 text-red-600" />;
      case 'high':
        return <AlertCircle className="w-6 h-6 text-orange-500" />;
      case 'medium':
        return <Info className="w-6 h-6 text-yellow-500" />;
      case 'low':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
    }
  };

  const getSeverityColor = () => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'high': return 'border-orange-500 bg-orange-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-green-500 bg-green-50';
    }
  };

  return (
    <div className={`border-2 rounded-lg p-4 ${getSeverityColor()}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {getSeverityIcon()}
          <div>
            <h3 className="font-semibold text-lg">{title}</h3>
            <p className="text-gray-600 mt-1">{description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold" style={{
            color: severity === 'critical' ? '#dc2626' : severity === 'high' ? '#f97316' : severity === 'medium' ? '#eab308' : '#22c55e'
          }}>
            {score}
          </span>
          <button onClick={() => setExpanded(!expanded)} className="p-1 hover:bg-gray-200 rounded">
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {expanded && recommendations.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <h4 className="font-medium text-gray-700 mb-2">Recommendations:</h4>
          <ul className="space-y-2">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm">
                <span className="text-blue-600">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

interface RiskDistributionChartProps {
  distribution: { critical: number; high: number; medium: number; low: number };
}

export const RiskDistributionChart: React.FC<RiskDistributionChartProps> = ({ distribution }) => {
  const total = distribution.critical + distribution.high + distribution.medium + distribution.low;
  
  const getBarColor = (type: string) => {
    switch (type) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-300';
    }
  };

  return (
    <div className="space-y-3">
      {[
        { key: 'critical', label: 'Critical' },
        { key: 'high', label: 'High' },
        { key: 'medium', label: 'Medium' },
        { key: 'low', label: 'Low' },
      ].map(({ key, label }) => {
        const count = distribution[key as keyof typeof distribution];
        const percentage = total > 0 ? (count / total) * 100 : 0;
        return (
          <div key={key} className="flex items-center gap-3">
            <span className="w-20 text-sm text-gray-600">{label}</span>
            <div className="flex-1 h-6 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getBarColor(key)} transition-all duration-500`}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="w-8 text-sm font-medium text-right">{count}</span>
          </div>
        );
      })}
    </div>
  );
};

interface ComplianceWarningBannerProps {
  warnings: Array<{
    title: string;
    message: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
  }>;
}

export const ComplianceWarningBanner: React.FC<ComplianceWarningBannerProps> = ({ warnings }) => {
  if (warnings.length === 0) return null;

  const criticalWarnings = warnings.filter(w => w.severity === 'critical' || w.severity === 'high');

  return (
    <div className="space-y-2">
      {criticalWarnings.map((warning, idx) => (
        <div
          key={idx}
          className={`flex items-center gap-3 p-3 rounded-lg ${
            warning.severity === 'critical' ? 'bg-red-100 border border-red-300' : 'bg-orange-100 border border-orange-300'
          }`}
        >
          <AlertTriangle className={`w-5 h-5 ${warning.severity === 'critical' ? 'text-red-600' : 'text-orange-600'}`} />
          <div className="flex-1">
            <span className="font-medium">{warning.title}: </span>
            <span className="text-sm text-gray-700">{warning.message}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

interface HiddenClauseAlertProps {
  clauses: Array<{
    title: string;
    text: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    explanation: string;
  }>;
}

export const HiddenClauseAlert: React.FC<HiddenClauseAlertProps> = ({ clauses }) => {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (clauses.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-red-700 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5" />
        Hidden Clauses Detected ({clauses.length})
      </h3>
      {clauses.map((clause, idx) => (
        <div key={idx} className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-medium text-red-800">{clause.title}</h4>
              <p className="text-sm text-red-700 mt-1">{clause.explanation}</p>
            </div>
            <button
              onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
              className="text-red-600 hover:bg-red-100 p-1 rounded"
            >
              {expandedIdx === idx ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>
          {expandedIdx === idx && (
            <div className="mt-3 pt-3 border-t border-red-200">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{clause.text}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

interface RiskAnalysisDashboardProps {
  analysisId: string;
  overallScore: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  risks: Array<{
    title: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    score: number;
    recommendations?: string[];
  }>;
  hiddenClauses: Array<{
    title: string;
    text: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    explanation: string;
  }>;
  warnings: Array<{
    title: string;
    message: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
  }>;
  distribution: { critical: number; high: number; medium: number; low: number };
}

export const RiskAnalysisDashboard: React.FC<RiskAnalysisDashboardProps> = ({
  overallScore,
  severity,
  risks,
  hiddenClauses,
  warnings,
  distribution,
}) => {
  return (
    <div className="space-y-6 p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Overall Risk Score</h2>
            <RiskScoreGauge score={overallScore} severity={severity} />
          </div>
        </div>
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Risk Distribution</h2>
            <RiskDistributionChart distribution={distribution} />
          </div>
        </div>
      </div>

      {warnings.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Compliance Warnings</h2>
          <ComplianceWarningBanner warnings={warnings} />
        </div>
      )}

      {hiddenClauses.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <HiddenClauseAlert clauses={hiddenClauses} />
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Identified Risks ({risks.length})</h2>
        <div className="space-y-4">
          {risks.map((risk, idx) => (
            <RiskCard
              key={idx}
              title={risk.title}
              severity={risk.severity}
              description={risk.description}
              score={risk.score}
              recommendations={risk.recommendations}
              expanded={risk.severity === 'critical' || risk.severity === 'high'}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default RiskAnalysisDashboard;