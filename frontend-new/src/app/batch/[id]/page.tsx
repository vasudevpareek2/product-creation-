'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient, Batch } from '@/lib/api';

export default function BatchDetail() {
  const params = useParams();
  const router = useRouter();
  const [batch, setBatch] = useState<Batch | null>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    loadBatch();
  }, [params.id]);

  const loadBatch = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getBatch(params.id as string);
      setBatch(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load batch');
    } finally {
      setLoading(false);
    }
  };

  const executeStage = async (stage: number, dryRun: boolean = false) => {
    if (!batch) return;

    try {
      setExecuting(true);
      setError(null);
      setLogs([]);

      const result = await apiClient.executeStage(batch.id, stage, dryRun);
      
      // Parse logs from result
      if (result.stdout) {
        setLogs(result.stdout.split('\n'));
      }

      // Reload batch to get updated status
      await loadBatch();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Stage execution failed');
    } finally {
      setExecuting(false);
    }
  };

  const canExecuteStage = (stage: number) => {
    if (!batch) return false;
    if (stage === 1) return batch.status === 'pending';
    if (stage === 2) return batch.status === 'stage1_completed';
    if (stage === 3) return batch.status === 'stage2_completed';
    return false;
  };

  const getStageStatus = (stage: number) => {
    if (!batch) return 'pending';
    if (stage === 1) return batch.status === 'stage1_completed' || batch.status === 'stage2_completed' || batch.status === 'stage3_completed' || batch.status === 'completed';
    if (stage === 2) return batch.status === 'stage2_completed' || batch.status === 'stage3_completed' || batch.status === 'completed';
    if (stage === 3) return batch.status === 'stage3_completed' || batch.status === 'completed';
    return false;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-gray-600">Loading batch details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!batch) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Batch not found</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-2 text-red-600 underline"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <button
          onClick={() => router.push('/dashboard')}
          className="text-blue-600 hover:text-blue-800 mb-6 inline-block"
        >
          ← Back to Dashboard
        </button>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">{batch.name}</h1>
              {batch.description && (
                <p className="text-gray-600">{batch.description}</p>
              )}
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              batch.status === 'completed' ? 'bg-green-100 text-green-800' :
              batch.status === 'failed' ? 'bg-red-100 text-red-800' :
              'bg-blue-100 text-blue-800'
            }`}>
              {batch.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Client ID:</span>
              <span className="ml-2 font-medium">{batch.client_id}</span>
            </div>
            <div>
              <span className="text-gray-500">Created:</span>
              <span className="ml-2 font-medium">{new Date(batch.created_at).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-500">Source File:</span>
              <span className="ml-2 font-medium">{batch.source_file.split('/').pop()}</span>
            </div>
            {batch.updated_at && (
              <div>
                <span className="text-gray-500">Last Updated:</span>
                <span className="ml-2 font-medium">{new Date(batch.updated_at).toLocaleString()}</span>
              </div>
            )}
          </div>

          {batch.error_message && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-red-800 text-sm">{batch.error_message}</p>
            </div>
          )}
        </div>

        {/* Workflow Stages */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Workflow Stages</h2>
          
          <div className="space-y-4">
            {/* Stage 1 */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium text-gray-800">Stage 1: Create Products & Variants</h3>
                {getStageStatus(1) && (
                  <span className="text-green-600">✓ Completed</span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Create products and variants from CSV files
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => executeStage(1, true)}
                  disabled={executing || !canExecuteStage(1)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed text-sm"
                >
                  Dry Run
                </button>
                <button
                  onClick={() => executeStage(1, false)}
                  disabled={executing || !canExecuteStage(1)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                >
                  Execute
                </button>
              </div>
            </div>

            {/* Stage 2 */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium text-gray-800">Stage 2: Enrich Products</h3>
                {getStageStatus(2) && (
                  <span className="text-green-600">✓ Completed</span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Rename products, add region tags, set visibility scopes
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => executeStage(2, true)}
                  disabled={executing || !canExecuteStage(2)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed text-sm"
                >
                  Dry Run
                </button>
                <button
                  onClick={() => executeStage(2, false)}
                  disabled={executing || !canExecuteStage(2)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                >
                  Execute
                </button>
              </div>
            </div>

            {/* Stage 3 */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium text-gray-800">Stage 3: Finalize Products</h3>
                {getStageStatus(3) && (
                  <span className="text-green-600">✓ Completed</span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Apply policies, vendors, pricing, and activate products
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => executeStage(3, true)}
                  disabled={executing || !canExecuteStage(3)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed text-sm"
                >
                  Dry Run
                </button>
                <button
                  onClick={() => executeStage(3, false)}
                  disabled={executing || !canExecuteStage(3)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                >
                  Execute
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Logs */}
        {logs.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Execution Logs</h2>
            <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
              {logs.map((log, index) => (
                <div key={index}>{log}</div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}