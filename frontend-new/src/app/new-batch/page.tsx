'use client';

import { useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';

export default function NewBatch() {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    client_id: '',
  });
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [uploadedFilePath, setUploadedFilePath] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    try {
      setUploading(true);
      setError(null);

      let result;
      if (file.name.endsWith('.csv')) {
        result = await apiClient.uploadCSV(file);
      } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        result = await apiClient.uploadExcel(file);
      } else {
        throw new Error('Invalid file type. Please upload CSV or Excel file.');
      }

      setUploadedFilePath(result.file_path);
      setSourceFile(file);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'File upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!uploadedFilePath) {
      setError('Please upload a source file first');
      return;
    }

    try {
      await apiClient.createBatch({
        name: formData.name,
        description: formData.description,
        client_id: formData.client_id,
        source_file: uploadedFilePath,
      });

      setSuccess(true);
      // Redirect to dashboard after a short delay
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create batch');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <Link href="/dashboard" className="text-blue-600 hover:text-blue-800 mb-6 inline-block">
            ← Back to Dashboard
          </Link>

          <h1 className="text-3xl font-bold text-gray-800 mb-2">Create New Batch</h1>
          <p className="text-gray-600 mb-8">Upload your source file and configure batch settings</p>

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <p className="text-green-800">Batch created successfully! Redirecting to dashboard...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Upload Source File</h2>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer"
              >
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-gray-600 mb-2">
                  {uploading ? 'Uploading...' : 'Click to upload or drag and drop'}
                </p>
                <p className="text-sm text-gray-500">CSV or Excel files only</p>
              </label>
            </div>

            {sourceFile && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  ✓ File uploaded: {sourceFile.name}
                </p>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Batch Configuration</h2>
            
            <div className="mb-4">
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Batch Name *
              </label>
              <input
                type="text"
                id="name"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Kerala Tours Batch 2024"
              />
            </div>

            <div className="mb-4">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="Optional description for this batch"
              />
            </div>

            <div className="mb-6">
              <label htmlFor="client_id" className="block text-sm font-medium text-gray-700 mb-2">
                Client ID *
              </label>
              <input
                type="text"
                id="client_id"
                required
                value={formData.client_id}
                onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 1"
              />
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={!uploadedFilePath || uploading}
                className="flex-1 bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Create Batch
              </button>
              <Link
                href="/dashboard"
                className="flex-1 bg-gray-200 text-gray-800 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium text-center"
              >
                Cancel
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}