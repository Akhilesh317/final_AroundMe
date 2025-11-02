'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { StarIcon, MapPinIcon, DollarSignIcon } from 'lucide-react'
import { formatDistance, formatPrice, formatRating } from '@/lib/utils'

// Mock data for demonstration
const mockPlaces = [
  {
    id: '1',
    name: 'Blue Bottle Coffee',
    category: 'cafe',
    rating: 4.5,
    user_rating_count: 1250,
    price_level: 2,
    distance_km: 0.5,
    score: 0.85,
    evidence: { rating: 0.45, reviews: 0.25, distance: 0.14 },
  },
  {
    id: '2',
    name: 'Philz Coffee',
    category: 'cafe',
    rating: 4.6,
    user_rating_count: 2100,
    price_level: 2,
    distance_km: 0.8,
    score: 0.88,
    evidence: { rating: 0.46, reviews: 0.28, distance: 0.12 },
  },
  {
    id: '3',
    name: 'Starbucks',
    category: 'cafe',
    rating: 4.2,
    user_rating_count: 800,
    price_level: 2,
    distance_km: 0.3,
    score: 0.79,
    evidence: { rating: 0.42, reviews: 0.20, distance: 0.15 },
  },
]

export default function ComparePage() {
  const [selectedPlaces] = useState(mockPlaces.slice(0, 3))

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Compare Places</h1>
        <p className="text-muted-foreground mb-8">
          Side-by-side comparison of selected places
        </p>

        {selectedPlaces.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">
                No places selected for comparison. Go back to search results to select places.
              </p>
              <Button className="mt-4" onClick={() => window.history.back()}>
                Back to Results
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Comparison Table */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {selectedPlaces.map((place) => (
                <Card key={place.id}>
                  <CardHeader>
                    <CardTitle className="text-lg">{place.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">{place.category}</p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Score */}
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Overall Score</p>
                      <Badge className="text-lg font-mono">{place.score.toFixed(2)}</Badge>
                    </div>

                    {/* Rating */}
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Rating</p>
                      <div className="flex items-center gap-1">
                        <StarIcon className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        <span className="font-semibold">{formatRating(place.rating)}</span>
                        <span className="text-sm text-muted-foreground">
                          ({place.user_rating_count})
                        </span>
                      </div>
                    </div>

                    {/* Price */}
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Price</p>
                      <p className="font-semibold">{formatPrice(place.price_level)}</p>
                    </div>

                    {/* Distance */}
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Distance</p>
                      <div className="flex items-center gap-1">
                        <MapPinIcon className="h-4 w-4" />
                        <span className="font-semibold">{formatDistance(place.distance_km)}</span>
                      </div>
                    </div>

                    {/* Evidence Breakdown */}
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Score Breakdown</p>
                      <div className="space-y-2">
                        {Object.entries(place.evidence).map(([key, value]) => (
                          <div key={key}>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="capitalize">{key}</span>
                              <span className="font-mono">{value.toFixed(3)}</span>
                            </div>
                            <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                              <div
                                className="h-full bg-primary"
                                style={{ width: `${(value / place.score) * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <Button className="w-full" asChild>
                      <a href={`/place/${place.id}`}>View Details</a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Feature Comparison Matrix */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Feature Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-3">Feature</th>
                        {selectedPlaces.map((place) => (
                          <th key={place.id} className="text-center py-2 px-3">
                            {place.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="py-2 px-3 font-medium">Overall Score</td>
                        {selectedPlaces.map((place) => (
                          <td key={place.id} className="text-center py-2 px-3">
                            {place.score.toFixed(2)}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b">
                        <td className="py-2 px-3 font-medium">Rating</td>
                        {selectedPlaces.map((place) => (
                          <td key={place.id} className="text-center py-2 px-3">
                            ⭐ {formatRating(place.rating)}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b">
                        <td className="py-2 px-3 font-medium">Reviews</td>
                        {selectedPlaces.map((place) => (
                          <td key={place.id} className="text-center py-2 px-3">
                            {place.user_rating_count}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b">
                        <td className="py-2 px-3 font-medium">Price</td>
                        {selectedPlaces.map((place) => (
                          <td key={place.id} className="text-center py-2 px-3">
                            {formatPrice(place.price_level)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 font-medium">Distance</td>
                        {selectedPlaces.map((place) => (
                          <td key={place.id} className="text-center py-2 px-3">
                            {formatDistance(place.distance_km)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}