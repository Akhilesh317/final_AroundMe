'use client'

import { useRouter } from 'next/navigation'  // ✅ Add this import
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Star, MapPin, DollarSign, ExternalLink, Phone } from 'lucide-react'

interface ResultCardProps {
  place: any
}

export function ResultCard({ place }: ResultCardProps) {
  const router = useRouter()  // ✅ Add this line

  const getPriceSymbol = (level: number) => {
    if (!level) return 'N/A'
    return '$'.repeat(level)
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-blue-600'
    if (score >= 0.4) return 'text-orange-600'
    return 'text-red-600'
  }

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-semibold line-clamp-1">{place.name}</h3>
            <p className="text-sm text-muted-foreground capitalize">{place.category}</p>
          </div>
          <Badge 
            variant="secondary" 
            className={`ml-2 font-bold ${getScoreColor(place.score)}`}
          >
            {place.score?.toFixed(2)}
          </Badge>
        </div>

        {/* Stats */}
        <div className="space-y-2 mb-4">
          {place.rating && (
            <div className="flex items-center gap-2 text-sm">
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              <span className="font-medium">{place.rating.toFixed(1)}</span>
              {place.user_rating_count && (
                <span className="text-muted-foreground">
                  ({place.user_rating_count.toLocaleString()})
                </span>
              )}
            </div>
          )}

          <div className="flex items-center gap-4 text-sm">
            {place.price_level && (
              <div className="flex items-center gap-1">
                <DollarSign className="h-4 w-4 text-green-600" />
                <span className="font-medium">{getPriceSymbol(place.price_level)}</span>
              </div>
            )}

            {place.distance_km !== undefined && (
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4 text-blue-600" />
                <span>{place.distance_km.toFixed(1)}km</span>
              </div>
            )}
          </div>
        </div>

        {/* Address */}
        {place.address && (
          <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
            {place.address}
          </p>
        )}

        {/* Provider Badges */}
        {place.provenance && place.provenance.length > 0 && (
          <div className="flex gap-1 mb-4">
            {place.provenance.map((source: any, index: number) => (
              <Badge key={index} variant="outline" className="text-xs">
                {source.provider}
              </Badge>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <Button 
            variant="default" 
            size="sm" 
            className="flex-1"
            onClick={() => router.push(`/place/${place.id}`)}  // ✅ Now works
          >
            View Details
          </Button>
          
          {place.phone && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => window.location.href = `tel:${place.phone}`}
            >
              <Phone className="h-4 w-4" />
            </Button>
          )}
          
          {(place.lat && place.lng) && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => window.open(
                `https://www.google.com/maps/dir/?api=1&destination=${place.lat},${place.lng}`,
                '_blank'
              )}
            >
              <MapPin className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Evidence Breakdown (Optional) */}
        {place.evidence && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs font-semibold mb-2">Score Evidence:</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {place.evidence.rating && (
                <div>
                  <span className="text-muted-foreground">Rating:</span>
                  <span className="ml-1 font-medium">+{place.evidence.rating.toFixed(3)}</span>
                </div>
              )}
              {place.evidence.reviews && (
                <div>
                  <span className="text-muted-foreground">Reviews:</span>
                  <span className="ml-1 font-medium">+{place.evidence.reviews.toFixed(3)}</span>
                </div>
              )}
              {place.evidence.distance && (
                <div>
                  <span className="text-muted-foreground">Distance:</span>
                  <span className="ml-1 font-medium">+{place.evidence.distance.toFixed(3)}</span>
                </div>
              )}
              {place.evidence.price_match !== undefined && (
                <div>
                  <span className="text-muted-foreground">Price:</span>
                  <span className="ml-1 font-medium">+{place.evidence.price_match.toFixed(3)}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}