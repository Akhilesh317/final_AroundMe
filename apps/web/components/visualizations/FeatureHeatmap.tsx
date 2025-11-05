'use client'

interface FeatureHeatmapProps {
  places: any[]
  featureAnalysis?: any
}

export function FeatureHeatmap({ places, featureAnalysis }: FeatureHeatmapProps) {
  // Use AI-generated features if available
  const features = featureAnalysis?.features || []
  const insights = featureAnalysis?.insights

  if (features.length === 0) {
    return (
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Feature Availability</h3>
        <div className="text-sm text-muted-foreground bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="font-medium mb-1">🤖 AI Feature Analysis</p>
          <p className="text-xs">
            Analyzing {places.length} places to determine likely features and amenities...
          </p>
        </div>
      </div>
    )
  }

  const getColor = (percentage: number) => {
    if (percentage >= 75) return { bg: 'bg-green-500', text: 'text-green-700', light: 'bg-green-50' }
    if (percentage >= 50) return { bg: 'bg-blue-500', text: 'text-blue-700', light: 'bg-blue-50' }
    if (percentage >= 25) return { bg: 'bg-yellow-500', text: 'text-yellow-700', light: 'bg-yellow-50' }
    return { bg: 'bg-orange-500', text: 'text-orange-700', light: 'bg-orange-50' }
  }

  const getRelevanceBadge = (relevance: string) => {
    if (relevance === 'high') return 'bg-green-100 text-green-700'
    if (relevance === 'medium') return 'bg-blue-100 text-blue-700'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold flex items-center gap-2">
            🤖 AI-Powered Feature Analysis
          </h3>
          <p className="text-xs text-muted-foreground">
            Intelligent predictions based on your search
          </p>
        </div>
        <div className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded font-medium">
          AI Generated
        </div>
      </div>

      {/* AI Insights */}
      {insights && (
        <div className="text-sm bg-gradient-to-r from-purple-50 to-blue-50 p-3 rounded-lg border border-purple-200">
          <p className="text-xs font-medium text-purple-900 mb-1">💡 AI Insights</p>
          <p className="text-xs text-purple-800">{insights}</p>
        </div>
      )}

      {/* Feature List */}
      <div className="space-y-2">
        {features.map((feature: any, index: number) => {
          const colors = getColor(feature.estimated_percentage)
          return (
            <div 
              key={index} 
              className={`space-y-2 hover:${colors.light} p-3 rounded-lg transition-all border border-transparent hover:border-gray-200`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-xl">{feature.icon}</span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{feature.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getRelevanceBadge(feature.relevance)}`}>
                        {feature.relevance}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {feature.reasoning}
                    </p>
                  </div>
                </div>
                <span className={`text-sm font-bold ${colors.text} ml-2`}>
                  ~{feature.estimated_percentage}%
                </span>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={`h-full ${colors.bg} transition-all`}
                    style={{ width: `${feature.estimated_percentage}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  ~{feature.count}/{places.length}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex gap-3 text-xs pt-3 border-t flex-wrap">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span>Very Likely (75%+)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span>Likely (50%+)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <span>Possible (25%+)</span>
        </div>
      </div>

      <div className="text-xs text-muted-foreground italic pt-2 border-t">
        * Percentages are AI-estimated based on place types, ratings, and search context
      </div>
    </div>
  )
}