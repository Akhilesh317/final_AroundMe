'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface PriceDistributionProps {
  places: any[]
}

export function PriceDistribution({ places }: PriceDistributionProps) {
  // Count places by price level
  const priceData = [
    { level: '$', count: 0, color: '#10b981' },
    { level: '$$', count: 0, color: '#3b82f6' },
    { level: '$$$', count: 0, color: '#f59e0b' },
    { level: '$$$$', count: 0, color: '#ef4444' },
  ]

  places.forEach(place => {
    if (place.price_level) {
      priceData[place.price_level - 1].count++
    }
  })

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Price Distribution</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={priceData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="level" />
          <YAxis />
          <Tooltip 
            contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
            labelStyle={{ fontWeight: 'bold' }}
          />
          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {priceData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}