import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, FileText, Shield, TrendingUp, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import RiskAnalysisDashboard from '../../components/risk/RiskAnalysisDashboard';

interface RiskAnalysisResult {
  analysis_id: string;
  status: string;
  overall_risk_score: number;
  overall_severity: string;
  critical_risks: number;
  high_risks: number;
  medium_risks: number;
  low_risks: number;
  total_risks: number;
  recommendations_count: number;
  hidden_clauses_count: number;
  financial_risks_count: number;
  technical_risks_count: number;
  compliance_risks_count: number;
  analysis_time_ms: number;
  confidence: number;
  summary?: string;
  key_findings: string[];
  warnings: string[];
}

interface RiskAnalysisPageProps {
  documentId?: string;
  documentText?: string;
}

const RiskAnalysisPage: React.FC<RiskAnalysisPageProps> = ({ documentId, documentText }) => {
  const navigate = useNavigate();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<RiskAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!documentText || documentText.length < 100) {
      setError('Document text is too short for analysis');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/risk/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentId || crypto.randomUUID(),
          document_text: documentText,
          include_hidden_clause_detection: true,
          include_financial_analysis: true,
          include_technical_analysis: true,
          include_compliance_check: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-600" />;
      default: return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-red-100 rounded-lg">
                <Shield className="w-8 h-8 text-red-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Risk Analysis</h1>
                <p className="text-gray-600">AI-powered tender document risk assessment</p>
              </div>
            </div>
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              Back
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {!result ? (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Ready to Analyze</h2>
              <p className="text-gray-600 max-w-lg mx-auto">
                Our AI will analyze your tender document for financial risks, hidden clauses, 
                technical risks, compliance issues, and more.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              {[
                { icon: FileText, label: 'Hidden Clauses', color: 'red' },
                { icon: TrendingUp, label: 'Financial Risks', color: 'orange' },
                { icon: Shield, label: 'Compliance', color: 'yellow' },
                { icon: Clock, label: 'Technical Risks', color: 'blue' },
              ].map((item, idx) => (
                <div key={idx} className={`flex items-center gap-3 p-4 bg-${item.color}-50 rounded-lg border border-${item.color}-200`}>
                  <item.icon className={`w-6 h-6 text-${item.color}-600`} />
                  <span className={`font-medium text-${item.color}-800`}>{item.label}</span>
                </div>
              ))}
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            <div className="flex justify-center">
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing || !documentText}
                className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-5 h-5" />
                    Start Risk Analysis
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  {getStatusIcon(result.status)}
                  <div>
                    <h2 className="text-lg font-semibold">Analysis Complete</h2>
                    <p className="text-sm text-gray-500">ID: {result.analysis_id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Analysis Time</p>
                    <p className="font-medium">{(result.analysis_time_ms / 1000).toFixed(2)}s</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Confidence</p>
                    <p className="font-medium">{(result.confidence * 100).toFixed(0)}%</p>
                  </div>
                  <button
                    onClick={() => setResult(null)}
                    className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                  >
                    New Analysis
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className={`p-4 rounded-lg ${getSeverityColor('critical')}`}>
                  <p className="text-sm font-medium">Critical</p>
                  <p className="text-2xl font-bold">{result.critical_risks}</p>
                </div>
                <div className={`p-4 rounded-lg ${getSeverityColor('high')}`}>
                  <p className="text-sm font-medium">High</p>
                  <p className="text-2xl font-bold">{result.high_risks}</p>
                </div>
                <div className={`p-4 rounded-lg ${getSeverityColor('medium')}`}>
                  <p className="text-sm font-medium">Medium</p>
                  <p className="text-2xl font-bold">{result.medium_risks}</p>
                </div>
                <div className={`p-4 rounded-lg ${getSeverityColor('low')}`}>
                  <p className="text-sm font-medium">Low</p>
                  <p className="text-2xl font-bold">{result.low_risks}</p>
                </div>
                <div className="p-4 rounded-lg bg-blue-50">
                  <p className="text-sm font-medium">Recommendations</p>
                  <p className="text-2xl font-bold text-blue-600">{result.recommendations_count}</p>
                </div>
              </div>
            </div>

            <RiskAnalysisDashboard
              analysisId={result.analysis_id}
              overallScore={result.overall_risk_score}
              severity={result.overall_severity as 'low' | 'medium' | 'high' | 'critical'}
              risks={[]}
              hiddenClauses={[]}
              warnings={result.warnings.map((w, i) => ({
                title: `Warning ${i + 1}`,
                message: w,
                severity: 'high' as const,
              }))}
              distribution={{
                critical: result.critical_risks,
                high: result.high_risks,
                medium: result.medium_risks,
                low: result.low_risks,
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskAnalysisPage;