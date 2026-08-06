'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

export default function TokenCapture() {
  const [tokenStatus, setTokenStatus] = useState<any>(null);
  const [capturing, setCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [adminUrl, setAdminUrl] = useState('https://admin.thrillophilia.com');
  const [clientId, setClientId] = useState('partners');

  useEffect(() => {
    checkTokenStatus();
  }, []);

  const checkTokenStatus = async () => {
    try {
      const status = await apiClient.getTokenStatus();
      setTokenStatus(status);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check token status');
    }
  };

  const startInteractiveCapture = async () => {
    try {
      setCapturing(true);
      setError(null);
      setSuccess(false);

      const result = await apiClient.captureTokenInteractive(adminUrl, clientId);
      
      if (result.success) {
        setSuccess(true);
        await checkTokenStatus();
        setTimeout(() => setSuccess(false), 5000);
      } else {
        setError(result.error || 'Token capture failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Token capture failed');
    } finally {
      setCapturing(false);
    }
  };

  const handleManualToken = async (token: string) => {
    try {
      await apiClient.uploadToken(token);
      setSuccess(true);
      await checkTokenStatus();
      setTimeout(() => setSuccess(false), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save token');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Token Capture</h1>
        <p className="text-gray-600 mb-8">Automatically capture Thrillophilia Access Token using browser automation</p>

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-green-800">Token captured and saved successfully!</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Token Status Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Current Token Status</h2>
          
          {tokenStatus ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Token File Exists:</span>
                <span className={`font-medium ${tokenStatus.exists ? 'text-green-600' : 'text-red-600'}`}>
                  {tokenStatus.exists ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Token Valid:</span>
                <span className={`font-medium ${tokenStatus.valid ? 'text-green-600' : 'text-red-600'}`}>
                  {tokenStatus.valid ? 'Yes' : 'No'}
                </span>
              </div>
              {tokenStatus.exists && (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Token Age:</span>
                    <span className="font-medium text-gray-800">
                      {tokenStatus.hours_old} hours
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Token Preview:</span>
                    <span className="font-mono text-sm text-gray-600">
                      {tokenStatus.token_preview}
                    </span>
                  </div>
                </>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Loading token status...</p>
          )}
        </div>

        {/* Interactive Capture */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Interactive Token Capture</h2>
          <p className="text-gray-600 mb-4">
            This will open a browser window where you can log in to the Thrillophilia admin panel. 
            The system will automatically capture your Access-Token once you're logged in.
          </p>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Admin URL</label>
              <input
                type="text"
                value={adminUrl}
                onChange={(e) => setAdminUrl(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://admin.thrillophilia.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Client ID</label>
              <input
                type="text"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="partners"
              />
            </div>
          </div>

          <button
            onClick={startInteractiveCapture}
            disabled={capturing}
            className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {capturing ? 'Capturing... (Browser window opened)' : 'Start Interactive Capture'}
          </button>

          {capturing && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="text-blue-800 text-sm">
                <strong>Instructions:</strong>
                <ol className="list-decimal list-inside mt-2 space-y-1">
                  <li>A browser window has opened</li>
                  <li>Log in to your Thrillophilia admin account</li>
                  <li>Navigate to any page that makes API calls</li>
                  <li>The token will be captured automatically</li>
                  <li>Close the browser window when done</li>
                </ol>
              </div>
            </div>
          )}
        </div>

        {/* Manual Token Entry */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Manual Token Entry</h2>
          <p className="text-gray-600 mb-4">
            If you already have an Access-Token, you can paste it here directly.
          </p>

          <ManualTokenForm onSave={handleManualToken} />
        </div>

        {/* Refresh Button */}
        <div className="mt-6 text-center">
          <button
            onClick={checkTokenStatus}
            className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Refresh Token Status
          </button>
        </div>
      </div>
    </div>
  );
}

function ManualTokenForm({ onSave }: { onSave: (token: string) => void }) {
  const [token, setToken] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;

    setSaving(true);
    await onSave(token);
    setSaving(false);
    setToken('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
        <textarea
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          rows={4}
          placeholder="Paste your Access-Token here..."
        />
      </div>
      <button
        type="submit"
        disabled={saving || !token.trim()}
        className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {saving ? 'Saving...' : 'Save Token'}
      </button>
    </form>
  );
}