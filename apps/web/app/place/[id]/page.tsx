'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  MapPin, 
  Phone, 
  ExternalLink, 
  Star, 
  DollarSign, 
  Navigation,
  Share2,
  Heart,
  Loader2,
  ArrowLeft
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface PlaceDetails {
  id: string
  name: string
  category: string
  rating: number
  user_rating_count: number
  price_level: number
  distance_km: number
  score: number
  lat: number
  lng: number
  address?: string
  phone?: string
  website?: string
  features?: { [key: string]: number }
  evidence?: {
    rating: number
    reviews: number
    distance: number
    price_match: number
    constraint_bonus: number
  }
  provenance?: Array<{
    provider: string
    provider_id: string
    name: string
  }>
}

async function fetchPlaceDetails(placeId: string): Promise<PlaceDetails> {
  const response = await fetch(`${API_URL}/api/places/${placeId}`)
  
  if (!response.ok) {
    throw new Error('Failed to fetch place details')
  }
  
  return response.json()
}

export default function PlaceDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const placeId = params.id as string

  const { data: place, isLoading, error } = useQuery({
    queryKey: ['place', placeId],
    queryFn: () => fetchPlaceDetails(placeId),
    enabled: !!placeId
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !place) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded">
          <p className="font-semibold">Error loading place details</p>
          <p className="text-sm">{error?.toString() || 'Place not found'}</p>
          <Button className="mt-4" onClick={() => router.back()}>
            Go Back
          </Button>
        </div>
      </div>
    )
  }

  const getPriceSymbol = (level: number) => {
    return '$'.repeat(level || 1)
  }

  const getFeaturePercentage = (value: number) => {
    return Math.round(value * 100)
  }

  const topFeatures = place.features 
    ? Object.entries(place.features)
        .map(([key, value]) => ({
          name: key.replace('feat_', '').replace(/_/g, ' '),
          percentage: getFeaturePercentage(value as number)
        }))
        .filter(f => f.percentage > 30)
        .sort((a, b) => b.percentage - a.percentage)
        .slice(0, 5)
    : []

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Results
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold">{place.name}</h1>
              <p className="text-muted-foreground capitalize mt-1">{place.category}</p>
            </div>
            
            <div className="flex gap-2">
              <Button variant="outline" size="icon">
                <Heart className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon">
                <Share2 className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4 mt-4">
            <div className="flex items-center gap-1">
              <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
              <span className="font-semibold">{place.rating?.toFixed(1) || 'N/A'}</span>
              <span className="text-muted-foreground">
                ({place.user_rating_count?.toLocaleString() || 0} reviews)
              </span>
            </div>

            <div className="flex items-center gap-1">
              <DollarSign className="h-5 w-5 text-green-600" />
              <span className="font-semibold">{getPriceSymbol(place.price_level)}</span>
            </div>

            <div className="flex items-center gap-1">
              <Navigation className="h-5 w-5 text-blue-600" />
              <span className="font-semibold">{place.distance_km?.toFixed(1) || '?'}km</span>
            </div>

            <Badge variant="secondary" className="text-base px-3 py-1">
              Score: {place.score?.toFixed(2) || 'N/A'}
            </Badge>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Contact & Location */}
            <Card>
              <CardContent className="p-6">
                <h2 className="text-xl font-bold mb-4">Contact & Location</h2>
                
                <div className="space-y-3">
                  {place.address && (
                    <div className="flex items-start gap-3">
                      <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                      <span>{place.address}</span>
                    </div>
                  )}

                  {place.phone && (
                    <div className="flex items-center gap-3">
                      <Phone className="h-5 w-5 text-muted-foreground" />
                      <a href={`tel:${place.phone}`} className="hover:underline">
                        {place.phone}
                      </a>
                    </div>
                  )}

                  {place.website && (
                    <div className="flex items-center gap-3">
                      <ExternalLink className="h-5 w-5 text-muted-foreground" />
                      <a 
                        href={place.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="hover:underline text-blue-600"
                      >
                        Visit Website
                      </a>
                    </div>
                  )}
                </div>

                <div className="flex gap-2 mt-6">
                  <Button 
                    className="flex-1"
                    onClick={() => window.open(
                      `https://www.google.com/maps/dir/?api=1&destination=${place.lat},${place.lng}`,
                      '_blank'
                    )}
                  >
                    <Navigation className="h-4 w-4 mr-2" />
                    Open in Maps
                  </Button>
                  {place.phone && (
                    <Button 
                      variant="outline"
                      onClick={() => window.location.href = `tel:${place.phone}`}
                    >
                      <Phone className="h-4 w-4 mr-2" />
                      Call
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Features & Amenities */}
            {topFeatures.length > 0 && (
              <Card>
                <CardContent className="p-6">
                  <h2 className="text-xl font-bold mb-4">Features & Amenities</h2>
                  
                  <div className="flex flex-wrap gap-2">
                    {topFeatures.map((feature) => (
                      <Badge 
                        key={feature.name} 
                        variant="secondary"
                        className="capitalize text-sm px-3 py-1"
                      >
                        {feature.name} ({feature.percentage}%)
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Data Sources */}
            {place.provenance && place.provenance.length > 0 && (
              <Card>
                <CardContent className="p-6">
                  <h2 className="text-xl font-bold mb-4">Data Sources</h2>
                  
                  <div className="space-y-2">
                    {place.provenance.map((source, index) => (
                      <div 
                        key={index}
                        className="flex items-center justify-between p-3 bg-secondary rounded-lg"
                      >
                        <div>
                          <p className="font-medium capitalize">{source.provider}</p>
                          <p className="text-sm text-muted-foreground">{source.name}</p>
                        </div>
                        <Badge variant="outline">{source.provider}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - Score & Actions */}
          <div className="space-y-6">
            {/* Score Breakdown */}
            {place.evidence && (
              <Card>
                <CardContent className="p-6">
                  <h2 className="text-xl font-bold mb-4">Score Breakdown</h2>
                  
                  <div className="space-y-3">
                    {Object.entries(place.evidence).map(([key, value]) => (
                      <div key={key}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm capitalize">
                            {key.replace(/_/g, ' ')}
                          </span>
                          <span className="text-sm font-semibold">
                            +{value.toFixed(3)}
                          </span>
                        </div>
                        <div className="h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${(value / 0.45) * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}

                    <div className="pt-3 border-t mt-4">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">Total Score</span>
                        <span className="text-xl font-bold">
                          {place.score?.toFixed(3) || 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Quick Actions */}
            <Card>
              <CardContent className="p-6">
                <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
                
                <div className="space-y-2">
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => {
                      navigator.clipboard.writeText(window.location.href)
                      alert('Link copied to clipboard!')
                    }}
                  >
                    <Share2 className="h-4 w-4 mr-2" />
                    Share Place
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                  >
                    <Heart className="h-4 w-4 mr-2" />
                    Save to Favorites
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}