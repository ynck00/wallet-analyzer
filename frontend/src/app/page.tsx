'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import Results component with SSR turned off
const Results = dynamic(() => import('@/components/Results').then(mod => mod.Results), {
  ssr: false,
  loading: () => <p className="text-lg animate-pulse">Loading analysis...</p>
});

// Define types for the analysis result
interface Pnl {
  realized: number;
  unrealized: number;
}

interface AnalysisResult {
  wallet_address: string;
  pnl: {
    '7d': Pnl;
    '30d': Pnl;
    '90d': Pnl;
    all_time: Pnl;
  };
  chart_data: { date: string; pnl: number }[];
  trade_ledger: any[];
}

export default function Home() {
  const [walletAddress, setWalletAddress] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyse = async () => {
    if (!walletAddress) {
      setError('Please enter a Solana wallet address.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ wallet_address: walletAddress }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch analysis from the backend.');
      }

      const data: AnalysisResult = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-8 pt-24 bg-gray-900 text-white">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-8 text-center w-full">Wallet Profitability Analyzer</h1>
      </div>

      <div className="w-full max-w-xl mb-8">
        <p className="text-center mb-6 text-gray-400">
          Enter a Solana wallet address to see how profitable you would have been if you had copied every trade in that wallet, with a 60-second delay.
        </p>
        <div className="flex gap-4">
          <input
            type="text"
            value={walletAddress}
            onChange={(e) => setWalletAddress(e.target.value)}
            placeholder="Enter Solana wallet address"
            className="flex-grow p-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleAnalyse}
            disabled={isLoading}
            className="p-3 bg-blue-600 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Analyzing...' : 'Analyse'}
          </button>
        </div>
        {error && <p className="text-red-500 text-center mt-4">{error}</p>}
      </div>

      {isLoading && !result && (
        <div className="mt-8">
          <p className="text-lg animate-pulse">Loading analysis...</p>
        </div>
      )}

      {result && <Results result={result} />}
    </main>
  );
}
