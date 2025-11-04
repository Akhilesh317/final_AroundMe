'use client'

import { Badge } from '@/components/ui/badge'

interface FeatureHeatmapProps {
  places: any[]
}

export function FeatureHeatmap({ places }: FeatureHeatmapProps) {
  // Collect all features and their availability
  const featureStats: { [key: string]: { count: number; avgScore: number } } = {}

  places.forEach(place => {
    if (place.features) {
      Object.entries(place.features).forEach(([key, value]) => {
        // Type guard to ensure value is a number
        const numValue = typeof value === 'number' ? value : 0
        
        if (!featureStats[key]) {
          featureStats[key] = { count: 0, avgScore: 0 }
        }
        if (numValue > 0.3) { // Only count if somewhat available
          featureStats[key].count++
          featureStats[key].avgScore += numValue
        }
      })
    }
  })

  // Calculate averages and sort
  const features = Object.entries(featureStats)
    .map(([key, stats]) => ({
      name: key.replace('feat_', '').replace(/_/g, ' '),
      count: stats.count,
      avgScore: stats.count > 0 ? stats.avgScore / stats.count : 0,
      percentage: (stats.count / places.length) * 100,
    }))
    .filter(f => f.count > 0)
    .sort((a, b) => b.count - a.count)
    .slice(0, 10) // Top 10 features

  const getColor = (percentage: number) => {
    if (percentage >= 75) return 'bg-green-500'
    if (percentage >= 50) return 'bg-blue-500'
    if (percentage >= 25) return 'bg-yellow-500'
    return 'bg-orange-500'
  }

  const getTextColor = (percentage: number) => {
    if (percentage >= 75) return 'text-green-700'
    if (percentage >= 50) return 'text-blue-700'
    if (percentage >= 25) return 'text-yellow-700'
    return 'text-orange-700'
  }

  if (features.length === 0) {
    return (
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Feature Availability</h3>
        <p className="text-xs text-muted-foreground">No feature data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Feature Availability</h3>
      <p className="text-xs text-muted-foreground">Most common features across all places</p>
      <div className="space-y-2 mt-3">
        {features.map((feature) => (
          <div key={feature.name} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="capitalize font-medium">{feature.name}</span>
              <span className={`font-semibold ${getTextColor(feature.percentage)}`}>
                {feature.count}/{places.length} ({feature.percentage.toFixed(0)}%)
              </span>
            </div>
            <div className="h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className={`h-full ${getColor(feature.percentage)} transition-all`}
                style={{ width: `${feature.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}