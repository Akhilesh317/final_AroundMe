'use client'

import { Card, CardContent } from '@/components/ui/card'
import { MapPin, Star, DollarSign, TrendingUp } from 'lucide-react'

interface QuickStatsProps {
  places: any[]
}

export function QuickStats({ places }: QuickStatsProps) {
  const avgRating = places.reduce((sum, p) => sum + (p.rating || 0), 0) / places.length
  const avgDistance = places.reduce((sum, p) => sum + (p.distance_km || 0), 0) / places.length
  const avgPrice = places.filter(p => p.price_level).reduce((sum, p) => sum + p.price_level, 0) / places.filter(p => p.price_level).length
  const avgScore = places.reduce((sum, p) => sum + (p.score || 0), 0) / places.length

  const stats = [
    {
      label: 'Avg Rating',
      value: avgRating.toFixed(1),
      icon: Star,
      color: 'text-yellow-600',
      suffix: '⭐'
    },
    {
      label: 'Avg Distance',
      value: avgDistance.toFixed(1),
      icon: MapPin,
      color: 'text-blue-600',
      suffix: 'km'
    },
    {
      label: 'Avg Price',
      value: '$'.repeat(Math.round(avgPrice)),
      icon: DollarSign,
      color: 'text-green-600',
      suffix: ''
    },
    {
      label: 'Match Score',
      value: (avgScore * 100).toFixed(0),
      icon: TrendingUp,
      color: 'text-purple-600',
      suffix: '%'
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {stats.map((stat) => (
        <Card key={stat.label}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
              <span className="text-xs text-muted-foreground">{stat.label}</span>
            </div>
            <div className="text-2xl font-bold">
              {stat.value}{stat.suffix}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}