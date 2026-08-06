'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

export default function AIAssistant() {
  const [aiStatus, setAiStatus] = useState<{ available: boolean; configured: boolean; model: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const [productData, setProductData] = useState({
    product_name: '',
    destination: '',
    activity_type: '',
    duration: '',
    special_features: '',
  });

  useEffect(() => {
    checkAIStatus();
  }, []);

  const checkAIStatus = async () => {
    try {
      const status = await apiClient.getAIStatus();
      setAiStatus(status);
      setLoading(false);
    } catch (err) {
      setError('Failed to check AI status');
      setLoading(false);
    }
  };

  const generateProductDescription = async () => {
    try {
      setGenerating(true);
      setError(null);
      setResult(null);

      const specialFeatures = productData.special_features
        ? productData.special_features.split(',').map(f => f.trim())
        : undefined;

      const response = await apiClient.generateProductDescription({
        product_name: productData.product_name,
        destination: productData.destination,
        activity_type: productData.activity_type,
        duration: productData.duration || undefined,
        special_features: specialFeatures,
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate content');
    } finally {
      setGenerating(false);
    }
  };

  const generateSEO = async () => {
    try {
      setGenerating(true);
      setError(null);
      setResult(null);

      const response = await apiClient.generateSEOContent({
        product_name: productData.product_name,
        destination: productData.destination,
        activity_type: productData.activity_type,
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate SEO content');
    } finally {
      setGenerating(false);
    }
  };

  const suggestProduct = async () => {
    try {
      setGenerating(true);
      setError(null);
      setResult(null);

      const response = await apiClient.suggestProduct({
        destination: productData.destination,
        activity_type: productData.activity_type,
        target_audience: undefined,
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to suggest product');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">AI Assistant</h1>
        <p className="text-gray-600 mb-8">Generate product content using Claude AI</p>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-gray-600">Checking AI status...</p>
          </div>
        )}

        {!loading && aiStatus && !aiStatus.configured && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <p className="text-yellow-800">
              Claude API is not configured. Please add ANTHROPIC_API_KEY to your backend .env file.
            </p>
          </div>
        )}

        {!loading && aiStatus && aiStatus.configured && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-green-800">
              ✓ Claude AI is configured and ready (Model: {aiStatus.model})
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Product Details</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Name</label>
                <input
                  type="text"
                  value={productData.product_name}
                  onChange={(e) => setProductData({ ...productData, product_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Kerala Backwaters Tour"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Destination</label>
                <input
                  type="text"
                  value={productData.destination}
                  onChange={(e) => setProductData({ ...productData, destination: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Kerala"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Activity Type</label>
                <input
                  type="text"
                  value={productData.activity_type}
                  onChange={(e) => setProductData({ ...productData, activity_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Houseboat Stay"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duration (Optional)</label>
                <input
                  type="text"
                  value={productData.duration}
                  onChange={(e) => setProductData({ ...productData, duration: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., 3 days 2 nights"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Special Features (Optional)</label>
                <input
                  type="text"
                  value={productData.special_features}
                  onChange={(e) => setProductData({ ...productData, special_features: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Sunset cruise, Traditional meal (comma-separated)"
                />
              </div>

              <div className="space-y-2 pt-4">
                <button
                  onClick={generateProductDescription}
                  disabled={generating || !aiStatus?.configured}
                  className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:bg-gray-400"
                >
                  {generating ? 'Generating...' : 'Generate Product Description'}
                </button>

                <button
                  onClick={generateSEO}
                  disabled={generating || !aiStatus?.configured}
                  className="w-full bg-purple-500 text-white py-3 rounded-lg hover:bg-purple-600 transition-colors font-medium disabled:bg-gray-400"
                >
                  {generating ? 'Generating...' : 'Generate SEO Content'}
                </button>

                <button
                  onClick={suggestProduct}
                  disabled={generating || !aiStatus?.configured}
                  className="w-full bg-orange-500 text-white py-3 rounded-lg hover:bg-orange-600 transition-colors font-medium disabled:bg-gray-400"
                >
                  {generating ? 'Generating...' : 'Suggest Product Structure'}
                </button>
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Generated Content</h2>
            
            {result && result.generated_content && (
              <div className="space-y-4">
                {result.generated_content.overview && (
                  <div>
                    <h3 className="font-medium text-gray-800 mb-2">Overview</h3>
                    <p className="text-gray-600 bg-gray-50 p-3 rounded-lg">{result.generated_content.overview}</p>
                  </div>
                )}

                {result.generated_content.long_description && (
                  <div>
                    <h3 className="font-medium text-gray-800 mb-2">Description</h3>
                    <p className="text-gray-600 bg-gray-50 p-3 rounded-lg">{result.generated_content.long_description}</p>
                  </div>
                )}

                {result.generated_content.highlights && (
                  <div>
                    <h3 className="font-medium text-gray-800 mb-2">Highlights</h3>
                    <ul className="list-disc list-inside text-gray-600 bg-gray-50 p-3 rounded-lg">
                      {result.generated_content.highlights.map((highlight: string, index: number) => (
                        <li key={index}>{highlight}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.generated_content.know_before_you_go && (
                  <div>
                    <h3 className="font-medium text-gray-800 mb-2">Know Before You Go</h3>
                    <ul className="list-disc list-inside text-gray-600 bg-gray-50 p-3 rounded-lg">
                      {result.generated_content.know_before_you_go.map((tip: string, index: number) => (
                        <li key={index}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.generated_content.meta_title && (
                  <div>
                    <h3 className="font-medium text-gray-800 mb-2">SEO Metadata</h3>
                    <div className="bg-gray-50 p-3 rounded-lg space-y-2">
                      <p><strong>Meta Title:</strong> {result.generated_content.meta_title}</p>
                      <p><strong>Meta Description:</strong> {result.generated_content.meta_description}</p>
                      <p><strong>OG Title:</strong> {result.generated_content.og_title}</p>
                      <p><strong>OG Description:</strong> {result.generated_content.og_description}</p>
                    </div>
                  </div>
                )}

                {result.tokens_used && (
                  <p className="text-sm text-gray-500 mt-4">Tokens used: {result.tokens_used}</p>
                )}
              </div>
            )}

            {!result && (
              <div className="text-center py-12 text-gray-500">
                Fill in the product details and click a generate button to see AI-generated content here
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}