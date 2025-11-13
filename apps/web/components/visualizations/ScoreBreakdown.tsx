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
    .filter(r => r.count > 0)
    .map(range => ({
      ...range,
      percentage: (range.count / places.length) * 100,
      value: range.count
    }))
    .reverse()

  // Calculate stats
  const avgScore = places.reduce((sum, p) => sum + (p.score || 0), 0) / places.length
  const topScorePlaces = places.filter(p => p.score >= 0.8).length

  // If no data, show simplified view
  if (radialData.length === 0) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-semibold">Match Score Distribution</h3>
        <p className="text-xs text-muted-foreground">No score data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
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

      {/* Simplified Bar Chart Instead of Radial */}
      <div className="space-y-2">
        {scoreRanges
          .filter(r => r.count > 0)
          .sort((a, b) => b.min - a.min)
          .map((range) => {
            const percentage = (range.count / places.length) * 100
            return (
              <div key={range.name} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium">{range.displayName}</span>
                  <span className="font-semibold" style={{ color: range.fill }}>
                    {range.count} ({percentage.toFixed(0)}%)
                  </span>
                </div>
                <div className="h-3 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full transition-all"
                    style={{ 
                      width: `${percentage}%`,
                      backgroundColor: range.fill
                    }}
                  />
                </div>
              </div>
            )
          })}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-2 pt-3 border-t">
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{topScorePlaces}</div>
          <div className="text-xs text-green-700">Excellent Matches</div>
        </div>
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">
            {((topScorePlaces / places.length) * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-blue-700">Success Rate</div>
        </div>
      </div>
    </div>
  )
}