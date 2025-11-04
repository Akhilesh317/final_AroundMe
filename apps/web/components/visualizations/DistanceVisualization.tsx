'use client'

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface DistanceVisualizationProps {
  places: any[]
}

export function DistanceVisualization({ places }: DistanceVisualizationProps) {
  // Prepare data: distance vs rating
  const scatterData = places
    .filter(p => p.distance_km !== undefined && p.rating)
    .map(place => ({
      distance: place.distance_km,
      rating: place.rating,
      name: place.name,
      score: place.score,
    }))

  // Color based on score
  const getColor = (score: number) => {
    if (score >= 0.8) return '#10b981' // Green
    if (score >= 0.6) return '#3b82f6' // Blue
    if (score >= 0.4) return '#f59e0b' // Orange
    return '#ef4444' // Red
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Distance vs Rating</h3>
      <p className="text-xs text-muted-foreground">Bubble size = match score</p>
      <ResponsiveContainer width="100%" height={250}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            type="number" 
            dataKey="distance" 
            name="Distance" 
            unit="km"
            label={{ value: 'Distance (km)', position: 'insideBottom', offset: -5 }}
          />
          <YAxis 
            type="number" 
            dataKey="rating" 
            name="Rating" 
            domain={[0, 5]}
            label={{ value: 'Rating', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
            formatter={(value: any, name: string) => {
              if (name === 'distance') return [`${value.toFixed(1)} km`, 'Distance']
              if (name === 'rating') return [`${value.toFixed(1)} ⭐`, 'Rating']
              return [value, name]
            }}
          />
          <Scatter data={scatterData} fill="#3b82f6">
            {scatterData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={getColor(entry.score)}
                fillOpacity={0.7}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div className="flex gap-3 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span>Excellent (0.8+)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span>Good (0.6+)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-orange-500"></div>
          <span>Fair (0.4+)</span>
        </div>
      </div>
    </div>
  )
}