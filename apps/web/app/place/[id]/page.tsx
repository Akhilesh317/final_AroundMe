'use client'

import { useParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  StarIcon,
  MapPinIcon,
  PhoneIcon,
  ExternalLinkIcon,
  DollarSignIcon,
} from 'lucide-react'
import { formatDistance, formatPrice, formatRating, getFeatureLabel } from '@/lib/utils'

// Mock data for demonstration - in production, fetch from API
const mockPlace = {
  id: '1',
  name: 'Blue Bottle Coffee',
  category: 'cafe',
  lat: 37.7749,
  lng: -122.4194,
  rating: 4.5,
  user_rating_count: 1250,
  price_level: 2,
  phone: '+1 415-123-4567',
  website: 'https://bluebottlecoffee.com',
  maps_url: 'https://maps.google.com/?cid=12345',
  address: '66 Mint St, San Francisco, CA 94103',
  distance_km: 0.5,
  features: {
    feat_wifi: 1.0,
    feat_outdoor_seating: 0.8,
    feat_family_friendly: 0.6,
  },
  score: 0.85,
  evidence: {
    rating: 0.45,
    reviews: 0.25,
    distance: 0.14,
    preferences: 0.01,
  },
  provenance: [
    {
      provider: 'google',
      provider_id: 'ChIJN1t_tDeuEmsRUsoyG83frY4',
      name: 'Blue Bottle Coffee',
      name_similarity: 1.0,
      geo_distance_m: 0.0,
      rating: 4.5,
      user_rating_count: 1250,
    },
  ],
  matched_partners: [],
}

export default function PlaceDetailPage() {
  const params = useParams()
  const place = mockPlace // In production: fetch based on params.id

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">{place.name}</h1>
          <p className="text-lg text-muted-foreground">{place.category}</p>

          <div className="flex flex-wrap items-center gap-4 mt-4">
            {place.rating && (
              <div className="flex items-center gap-2">
                <StarIcon className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                <span className="text-lg font-semibold">
                  {formatRating(place.rating)}
                </span>
                {place.user_rating_count && (
                  <span className="text-sm text-muted-foreground">
                    ({place.user_rating_count} reviews)
                  </span>
                )}
              </div>
            )}

            {place.price_level && (
              <Badge variant="outline" className="text-base">
                {formatPrice(place.price_level)}
              </Badge>
            )}

            {place.distance_km !== undefined && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPinIcon className="h-5 w-5" />
                <span>{formatDistance(place.distance_km)}</span>
              </div>
            )}

            <Badge variant="secondary" className="text-sm">
              Score: {place.score.toFixed(2)}
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="md:col-span-2 space-y-6">
            {/* Contact Info */}
            <Card>
              <CardHeader>
                <CardTitle>Contact & Location</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {place.address && (
                  <div className="flex items-start gap-3">
                    <MapPinIcon className="h-5 w-5 text-muted-foreground mt-0.5" />
                    <p className="text-sm">{place.address}</p>
                  </div>
                )}

                {place.phone && (
                  <div className="flex items-center gap-3">
                    <PhoneIcon className="h-5 w-5 text-muted-foreground" />
                    <a href={`tel:${place.phone}`} className="text-sm hover:underline">
                      {place.phone}
                    </a>
                  </div>
                )}

                {place.website && (
                  <div className="flex items-center gap-3">
                    <ExternalLinkIcon className="h-5 w-5 text-muted-foreground" />
                    
                      <a href={place.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm hover:underline"
                    >
                      Visit Website
                    </a>
                  </div>
                )}

                <div className="flex gap-2 pt-3">
                  {place.maps_url && (
                    <Button asChild className="flex-1">
                      <a href={place.maps_url} target="_blank" rel="noopener noreferrer">
                        Open in Maps
                      </a>
                    </Button>
                  )}
                  {place.phone && (
                    <Button asChild variant="outline">
                      <a href={`tel:${place.phone}`}>Call</a>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Features */}
            {Object.keys(place.features).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Features & Amenities</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(place.features)
                      .filter(([_, value]) => value > 0.5)
                      .map(([key, value]) => (
                        <Badge key={key} variant="secondary">
                          {getFeatureLabel(key)}
                          <span className="ml-1 text-xs opacity-70">
                            ({Math.round(value * 100)}%)
                          </span>
                        </Badge>
                      ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Provenance */}
            <Card>
              <CardHeader>
                <CardTitle>Data Sources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {place.provenance.map((prov, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline" className="capitalize">
                          {prov.provider}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {(prov.name_similarity * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <div className="space-y-1 text-sm">
                        <p>
                          <span className="text-muted-foreground">Name:</span> {prov.name}
                        </p>
                        {prov.rating && (
                          <p>
                            <span className="text-muted-foreground">Rating:</span>{' '}
                            {formatRating(prov.rating)}
                            {prov.user_rating_count && ` (${prov.user_rating_count})`}
                          </p>
                        )}
                        <p>
                          <span className="text-muted-foreground">Distance:</span>{' '}
                          {prov.geo_distance_m.toFixed(0)}m
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Score Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Score Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(place.evidence).map(([key, value]) => (
                    <div key={key}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm capitalize">
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span className="text-sm font-mono">
                          {value >= 0 ? '+' : ''}
                          {value.toFixed(3)}
                        </span>
                      </div>
                      <div className="h-2 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary"
                          style={{
                            width: `${Math.abs(value) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                  <div className="border-t pt-3 mt-3">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">Total Score</span>
                      <span className="font-mono font-semibold">
                        {place.score.toFixed(3)}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" className="w-full justify-start">
                  Share Place
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  Save to Favorites
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  Report Issue
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}