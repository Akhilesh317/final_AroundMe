import { Badge } from './ui/badge'
import { MapPinIcon } from 'lucide-react'
import { MatchedPartner } from '@/lib/types'
import { formatDistance } from '@/lib/utils'

interface PartnerBadgeProps {
  partner: MatchedPartner
}

export function PartnerBadge({ partner }: PartnerBadgeProps) {
  return (
    <div className="flex items-start gap-2 p-2 border rounded-lg text-sm">
      <MapPinIcon className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{partner.name}</p>
        <p className="text-xs text-muted-foreground">
          {partner.kind} • {formatDistance(partner.distance_m / 1000)}
        </p>
        {partner.matched_must_haves.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {partner.matched_must_haves.map((feature, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {feature.replace(/_/g, ' ')}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}