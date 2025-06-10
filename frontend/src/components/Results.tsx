'use client';

import dynamic from 'next/dynamic';
import Papa from 'papaparse';

// Dynamically import PnlChart with SSR turned off
const PnlChart = dynamic(() => import('./PnlChart').then((mod) => mod.PnlChart), {
  ssr: false,
  loading: () => <p className="text-center">Loading chart...</p>,
});

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

interface ResultsProps {
  result: AnalysisResult;
}

const PnlCard = ({ title, pnl }: { title: string; pnl: Pnl }) => (
  <div className="bg-gray-700 p-4 rounded-lg">
    <h3 className="text-lg font-bold text-gray-300">{title}</h3>
    <p className={`text-xl ${pnl.realized >= 0 ? 'text-green-400' : 'text-red-400'}`}>
      Realized: ${pnl.realized.toFixed(2)}
    </p>
    <p className={`text-xl ${pnl.unrealized >= 0 ? 'text-green-400' : 'text-red-400'}`}>
      Unrealized: ${pnl.unrealized.toFixed(2)}
    </p>
  </div>
);

export const Results = ({ result }: ResultsProps) => {
  const handleDownload = () => {
    const csv = Papa.unparse(result.trade_ledger, {
      columns: ["timestamp", "type", "from_token", "to_token", "price_after_60s", "profit_or_loss"]
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.href) {
      URL.revokeObjectURL(link.href);
    }
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.setAttribute('download', `trade-ledger-${result.wallet_address}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="mt-12 w-full max-w-5xl bg-gray-800 p-8 rounded-lg animate-fade-in">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">
          Analysis for: <span className="font-mono text-lg bg-gray-900 px-2 py-1 rounded">{result.wallet_address}</span>
        </h2>
        <button
          onClick={handleDownload}
          className="p-2 bg-green-600 rounded-lg font-semibold hover:bg-green-700 transition-colors"
        >
          Download Ledger (CSV)
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <PnlCard title="Last 7 Days" pnl={result.pnl['7d'] ?? { realized: 0, unrealized: 0 }} />
        <PnlCard title="Last 30 Days" pnl={result.pnl['30d'] ?? { realized: 0, unrealized: 0 }} />
        <PnlCard title="Last 90 Days" pnl={result.pnl['90d'] ?? { realized: 0, unrealized: 0 }} />
        <PnlCard title="All Time" pnl={result.pnl.all_time ?? { realized: 0, unrealized: 0 }} />
      </div>

      <h3 className="text-xl font-bold mb-4">Performance Chart</h3>
      <PnlChart data={result.chart_data} />

      <h3 className="text-xl font-bold mt-8 mb-4">Trade Ledger</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-gray-900 rounded-lg">
          <thead>
            <tr className="text-left text-gray-400">
              <th className="p-3">Timestamp</th>
              <th className="p-3">Type</th>
              <th className="p-3">From Token</th>
              <th className="p-3">To Token</th>
              <th className="p-3">Price (+60s)</th>
              <th className="p-3">Profit/Loss</th>
            </tr>
          </thead>
          <tbody>
            {result.trade_ledger.map((trade, index) => (
              <tr key={index} className="border-t border-gray-800 hover:bg-gray-700">
                <td className="p-3 font-mono">{new Date(trade.timestamp * 1000).toLocaleString()}</td>
                <td className="p-3">{trade.type}</td>
                <td className="p-3 font-mono text-sm">{trade.from_token}</td>
                <td className="p-3 font-mono text-sm">{trade.to_token}</td>
                <td className="p-3">${trade.price_after_60s.toFixed(2)}</td>
                <td className={`p-3 font-bold ${trade.profit_or_loss >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  ${trade.profit_or_loss.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <style jsx>{`
        .animate-fade-in {
          animation: fadeIn 0.5s ease-in-out;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}; 