'use client'

interface CategoryBreakdownProps {
  places: any[]
}

const COLORS = [
  { bg: 'bg-blue-500', text: 'text-blue-700', light: 'bg-blue-50' },
  { bg: 'bg-green-500', text: 'text-green-700', light: 'bg-green-50' },
  { bg: 'bg-orange-500', text: 'text-orange-700', light: 'bg-orange-50' },
  { bg: 'bg-red-500', text: 'text-red-700', light: 'bg-red-50' },
  { bg: 'bg-purple-500', text: 'text-purple-700', light: 'bg-purple-50' },
  { bg: 'bg-pink-500', text: 'text-pink-700', light: 'bg-pink-50' },
  { bg: 'bg-cyan-500', text: 'text-cyan-700', light: 'bg-cyan-50' },
  { bg: 'bg-lime-500', text: 'text-lime-700', light: 'bg-lime-50' },
]

export function CategoryBreakdown({ places }: CategoryBreakdownProps) {
  const categoryCount: { [key: string]: number } = {}
  
  places.forEach(place => {
    const category = place.category || 'Other'
    categoryCount[category] = (categoryCount[category] || 0) + 1
  })

  const categories = Object.entries(categoryCount)
    .map(([name, count]) => ({ 
      name: name.charAt(0).toUpperCase() + name.slice(1),
      count,
      percentage: (count / places.length) * 100
    }))
    .sort((a, b) => b.count - a.count)

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold">Category Breakdown</h3>
      <p className="text-xs text-muted-foreground">
        {places.length} places across {categories.length} categories
      </p>

      {/* Stacked Bar */}
      <div className="h-8 flex rounded-lg overflow-hidden shadow-sm">
        {categories.map((category, index) => (
          <div
            key={category.name}
            className={`${COLORS[index % COLORS.length].bg} transition-all hover:opacity-80 cursor-pointer`}
            style={{ width: `${category.percentage}%` }}
            title={`${category.name}: ${category.count} (${category.percentage.toFixed(1)}%)`}
          />
        ))}
      </div>

      {/* Legend with bars */}
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {categories.map((category, index) => (
          <div key={category.name} className="flex items-center justify-between hover:bg-secondary/50 p-2 rounded transition-colors">
            <div className="flex items-center gap-2 flex-1">
              <div className={`w-3 h-3 rounded-full ${COLORS[index % COLORS.length].bg}`} />
              <span className="text-sm font-medium">{category.name}</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-32 h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className={`h-full ${COLORS[index % COLORS.length].bg} transition-all`}
                  style={{ width: `${category.percentage}%` }}
                />
              </div>
              <span className={`text-sm font-semibold w-20 text-right ${COLORS[index % COLORS.length].text}`}>
                {category.count} ({category.percentage.toFixed(0)}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}