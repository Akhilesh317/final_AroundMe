'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface RatingDistributionProps {
  places: any[]
}

export function RatingDistribution({ places }: RatingDistributionProps) {
  // Group by rating ranges
  const ratingRanges = [
    { range: '4.5-5.0', min: 4.5, max: 5.0, count: 0 },
    { range: '4.0-4.4', min: 4.0, max: 4.4, count: 0 },
    { range: '3.5-3.9', min: 3.5, max: 3.9, count: 0 },
    { range: '3.0-3.4', min: 3.0, max: 3.4, count: 0 },
    { range: '<3.0', min: 0, max: 2.9, count: 0 },
  ]

  places.forEach(place => {
    if (place.rating) {
      const range = ratingRanges.find(r => place.rating >= r.min && place.rating <= r.max)
      if (range) range.count++
    }
  })

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Rating Distribution</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={ratingRanges} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis type="number" />
          <YAxis dataKey="range" type="category" width={60} />
          <Tooltip 
            contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
          />
          <Bar dataKey="count" fill="#f59e0b" radius={[0, 8, 8, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}