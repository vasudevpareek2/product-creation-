'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient, PartnerConfig } from '@/lib/api';

export default function Config() {
  const [configs, setConfigs] = useState<any[]>([]);
  const [selectedPartner, setSelectedPartner] = useState<string>('');
  const [config, setConfig] = useState<PartnerConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listConfigs();
      setConfigs(data.configs || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configs');
    } finally {
      setLoading(false);
    }
  };

  const loadConfig = async (partnerId: string) => {
    try {
      setLoading(true);
      const data = await apiClient.getConfig(partnerId);
      setConfig(data.config);
      setSelectedPartner(partnerId);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load config');
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config || !selectedPartner) return;

    try {
      setSaving(true);
      setError(null);
      await apiClient.saveConfig(selectedPartner, config);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      loadConfigs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save config');
    } finally {
      setSaving(false);
    }
  };

  const handleTokenUpload = async (token: string) => {
    try {
      await apiClient.uploadToken(token);
      alert('Token saved successfully');
    } catch (err) {
      alert('Failed to save token: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Configuration</h1>
        <p className="text-gray-600 mb-8">Manage partner configurations and settings</p>

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-green-800">Configuration saved successfully!</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Partner List */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Partners</h2>
            
            <div className="mb-4">
              <input
                type="text"
                placeholder="New Partner ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    const target = e.target as HTMLInputElement;
                    if (target.value) {
                      loadConfig(target.value);
                      target.value = '';
                    }
                  }
                }}
              />
            </div>

            <div className="space-y-2">
              {configs.map((cfg) => (
                <button
                  key={cfg.partner_id}
                  onClick={() => loadConfig(cfg.partner_id)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                    selectedPartner === cfg.partner_id
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="font-medium">{cfg.partner_id}</div>
                  <div className="text-sm text-gray-600">{cfg.region_name || 'No region'}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Config Editor */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              {selectedPartner ? `Edit Config: ${selectedPartner}` : 'Select a partner to edit'}
            </h2>

            {config && (
              <div className="space-y-6">
                {/* Basic Settings */}
                <div>
                  <h3 className="text-lg font-medium text-gray-800 mb-3">Basic Settings</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Client ID</label>
                      <input
                        type="text"
                        value={config.client_id}
                        onChange={(e) => setConfig({ ...config, client_id: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Region Name</label>
                      <input
                        type="text"
                        value={config.region_name || ''}
                        onChange={(e) => setConfig({ ...config, region_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>
                </div>

                {/* Vendors */}
                <div>
                  <h3 className="text-lg font-medium text-gray-800 mb-3">Vendors</h3>
                  <div className="space-y-2">
                    {config.vendor_names.map((vendor, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={vendor}
                          onChange={(e) => {
                            const newVendors = [...config.vendor_names];
                            newVendors[index] = e.target.value;
                            setConfig({ ...config, vendor_names: newVendors });
                          }}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                        />
                        <button
                          onClick={() => {
                            const newVendors = config.vendor_names.filter((_, i) => i !== index);
                            setConfig({ ...config, vendor_names: newVendors });
                          }}
                          className="px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                    <button
                      onClick={() => setConfig({ ...config, vendor_names: [...config.vendor_names, ''] })}
                      className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                    >
                      + Add Vendor
                    </button>
                  </div>
                </div>

                {/* Business Terms */}
                <div>
                  <h3 className="text-lg font-medium text-gray-800 mb-3">Business Terms</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Margin</label>
                      <input
                        type="number"
                        step="0.01"
                        value={config.margin}
                        onChange={(e) => setConfig({ ...config, margin: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                      <input
                        type="text"
                        value={config.currency}
                        onChange={(e) => setConfig({ ...config, currency: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Reseller Partner ID</label>
                      <input
                        type="number"
                        value={config.reseller_partner_id || ''}
                        onChange={(e) => setConfig({ ...config, reseller_partner_id: parseInt(e.target.value) || undefined })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Inventory ID</label>
                      <input
                        type="number"
                        value={config.inventory_id || ''}
                        onChange={(e) => setConfig({ ...config, inventory_id: parseInt(e.target.value) || undefined })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>
                </div>

                {/* Access Token */}
                <div>
                  <h3 className="text-lg font-medium text-gray-800 mb-3">Access Token</h3>
                  <div className="mb-3">
                    <Link
                      href="/token-capture"
                      className="inline-block bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm"
                    >
                      Auto-Capture Token
                    </Link>
                    <span className="ml-2 text-sm text-gray-500">or paste manually below</span>
                  </div>
                  <textarea
                    placeholder="Paste your Thrillophilia Access Token here"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    rows={3}
                    onChange={(e) => handleTokenUpload(e.target.value)}
                  />
                  <p className="text-sm text-gray-500 mt-1">Token will be saved automatically when you paste it</p>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={saveConfig}
                    disabled={saving}
                    className="flex-1 bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:bg-gray-400"
                  >
                    {saving ? 'Saving...' : 'Save Configuration'}
                  </button>
                </div>
              </div>
            )}

            {!selectedPartner && (
              <div className="text-center py-12 text-gray-500">
                Select a partner from the list to edit their configuration
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}