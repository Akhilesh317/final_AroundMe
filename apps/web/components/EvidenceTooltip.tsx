'use client'

import { useState } from 'react'
import { Badge } from './ui/badge'
import { InfoIcon } from 'lucide-react'

interface EvidenceTooltipProps {
  evidence: Record<string, number>
  score: number
}

export function EvidenceTooltip({ evidence, score }: EvidenceTooltipProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className="relative">
      <div
        className="flex items-center gap-1 cursor-help"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <Badge variant="default" className="font-mono">
          {score.toFixed(2)}
        </Badge>
        <InfoIcon className="h-4 w-4 text-muted-foreground" />
      </div>

      {showTooltip && (
        <div className="absolute right-0 top-8 z-50 w-64 p-3 bg-popover border rounded-lg shadow-lg">
          <p className="text-sm font-semibold mb-2">Score Breakdown</p>
          <div className="space-y-1">
            {Object.entries(evidence).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-mono">
                  {value >= 0 ? '+' : ''}
                  {value.toFixed(3)}
                </span>
              </div>
            ))}
            <div className="border-t pt-1 mt-2 flex items-center justify-between text-sm font-semibold">
              <span>Total Score</span>
              <span className="font-mono">{score.toFixed(3)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}