'use client'

import Link from 'next/link'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { MapPinIcon, StarIcon, PhoneIcon, ExternalLinkIcon } from 'lucide-react'
import { formatDistance, formatPrice, formatRating } from '@/lib/utils'
import { Place } from '@/lib/types'
import { PartnerBadge } from './PartnerBadge'
import { EvidenceTooltip } from './EvidenceTooltip'

interface ResultCardProps {
  place: Place
}

export function ResultCard({ place }: ResultCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{place.name}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {place.category || 'Place'}
            </p>
          </div>
          <EvidenceTooltip evidence={place.evidence} score={place.score} />
        </div>

        {/* Rating and Price */}
        <div className="flex items-center gap-3 mt-2">
          {place.rating && (
            <div className="flex items-center gap-1">
              <StarIcon className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              <span className="text-sm font-medium">
                {formatRating(place.rating)}
              </span>
              {place.user_rating_count && (
                <span className="text-xs text-muted-foreground">
                  ({place.user_rating_count})
                </span>
              )}
            </div>
          )}

          {place.price_level && (
            <Badge variant="outline">{formatPrice(place.price_level)}</Badge>
          )}

          {place.distance_km !== undefined && (
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <MapPinIcon className="h-4 w-4" />
              {formatDistance(place.distance_km)}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Address */}
        {place.address && (
          <p className="text-sm text-muted-foreground">{place.address}</p>
        )}

        {/* Features */}
        {Object.keys(place.features).length > 0 && (
          <div className="flex flex-wrap gap-1">
            {Object.entries(place.features)
              .filter(([_, value]) => value > 0.5)
              .slice(0, 4)
              .map(([key, value]) => (
                <Badge key={key} variant="secondary" className="text-xs">
                  {key.replace('feat_', '').replace(/_/g, ' ')}
                </Badge>
              ))}
          </div>
        )}

        {/* Matched Partners */}
        {place.matched_partners.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Nearby Partners:</p>
            {place.matched_partners.map((partner, index) => (
              <PartnerBadge key={index} partner={partner} />
            ))}
          </div>
        )}

        {/* Provenance */}
        <div className="flex gap-1">
          {place.provenance.map((prov, index) => (
            <Badge key={index} variant="outline" className="text-xs">
              {prov.provider}
            </Badge>
          ))}
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button asChild size="sm" className="flex-1">
          <Link href={`/place/${place.id}`}>View Details</Link>
        </Button>

        {place.maps_url && (
          <Button asChild size="sm" variant="outline">
            <a href={place.maps_url} target="_blank" rel="noopener noreferrer">
              <ExternalLinkIcon className="h-4 w-4" />
            </a>
          </Button>
        )}

        {place.phone && (
          <Button asChild size="sm" variant="outline">
            <a href={`tel:${place.phone}`}>
              <PhoneIcon className="h-4 w-4" />
            </a>
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}