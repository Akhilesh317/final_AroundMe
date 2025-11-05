'use client'

import { RadialBarChart, RadialBar, Legend, ResponsiveContainer, Tooltip, PolarAngleAxis } from 'recharts'

interface ScoreBreakdownProps {
  places: any[]
}

export function ScoreBreakdown({ places }: ScoreBreakdownProps) {
  // Group places by score ranges
  const scoreRanges = [
    { name: 'Excellent', min: 0.8, max: 1.0, count: 0, fill: '#10b981', displayName: '⭐ Excellent (0.8+)' },
    { name: 'Great', min: 0.7, max: 0.79, count: 0, fill: '#3b82f6', displayName: '✨ Great (0.7-0.8)' },
    { name: 'Good', min: 0.6, max: 0.69, count: 0, fill: '#f59e0b', displayName: '👍 Good (0.6-0.7)' },
    { name: 'Fair', min: 0.5, max: 0.59, count: 0, fill: '#ef4444', displayName: '👌 Fair (0.5-0.6)' },
    { name: 'Poor', min: 0, max: 0.49, count: 0, fill: '#6b7280', displayName: '😐 Below Average' },
  ]

  places.forEach(place => {
    const score = place.score || 0
    const range = scoreRanges.find(r => score >= r.min && score <= r.max)
    if (range) range.count++
  })

  // Convert to percentage for radial chart
  const radialData = scoreRanges
    .filter(r => r.count > 0) // Only show ranges with data
    .map(range => ({
      ...range,
      percentage: (range.count / places.length) * 100,
      value: range.count
    }))
    .reverse() // Display from inside to outside (worst to best)

  // Calculate stats
  const avgScore = places.reduce((sum, p) => sum + (p.score || 0), 0) / places.length
  const topScorePlaces = places.filter(p => p.score >= 0.8).length

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Match Score Distribution</h3>
          <p className="text-xs text-muted-foreground">How well places match your search</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-purple-600">{(avgScore * 100).toFixed(0)}%</div>
          <div className="text-xs text-muted-foreground">Avg Score</div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <RadialBarChart 
          cx="50%" 
          cy="50%" 
          innerRadius="20%" 
          outerRadius="90%" 
          data={radialData}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar
            background
            dataKey="percentage"
            cornerRadius={10}
            label={{ 
              position: 'insideStart', 
              fill: '#fff', 
              fontSize: 11,
              fontWeight: 'bold',
              formatter: (value: number) => `${value.toFixed(0)}%`
            }}
          />
          <Legend 
            iconSize={12}
            layout="vertical"
            verticalAlign="middle"
            align="right"
            wrapperStyle={{ paddingLeft: '10px' }}
            formatter={(value, entry: any) => (
              <span className="text-xs">
                {entry.payload.displayName}
                <span className="font-semibold ml-1">({entry.payload.value})</span>
              </span>
            )}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #e5e7eb', 
              borderRadius: '8px',
              padding: '8px 12px'
            }}
            formatter={(value: any, name: string, props: any) => [
              `${props.payload.count} places (${value.toFixed(1)}%)`,
              props.payload.displayName
            ]}
          />
        </RadialBarChart>
      </ResponsiveContainer>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-2 pt-2 border-t">
        <div className="text-center p-2 bg-green-50 rounded">
          <div className="text-lg font-bold text-green-600">{topScorePlaces}</div>
          <div className="text-xs text-green-700">Excellent Matches</div>
        </div>
        <div className="text-center p-2 bg-blue-50 rounded">
          <div className="text-lg font-bold text-blue-600">
            {((topScorePlaces / places.length) * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-blue-700">Success Rate</div>
        </div>
      </div>
    </div>
  )
}