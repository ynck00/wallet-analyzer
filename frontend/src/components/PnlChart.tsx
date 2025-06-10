'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PnlChartProps {
  data: { date: string; pnl: number }[];
}

export const PnlChart = ({ data }: PnlChartProps) => {
  return (
    <div className="bg-gray-900 p-4 rounded-lg" style={{ width: '100%', height: 400 }}>
      <ResponsiveContainer>
        <LineChart
          data={data}
          margin={{
            top: 5, right: 30, left: 20, bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
          <XAxis dataKey="date" stroke="#A0AEC0" />
          <YAxis stroke="#A0AEC0" />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1A202C', border: '1px solid #2D3748' }} 
            labelStyle={{ color: '#E2E8F0' }}
          />
          <Legend wrapperStyle={{ color: '#E2E8F0' }} />
          <Line type="monotone" dataKey="pnl" stroke="#38B2AC" strokeWidth={2} activeDot={{ r: 8 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}; 