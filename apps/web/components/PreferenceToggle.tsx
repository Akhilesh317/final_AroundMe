'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

interface PreferenceToggleProps {
  enabled: boolean
  onToggle: (enabled: boolean) => void
}

export function PreferenceToggle({ enabled, onToggle }: PreferenceToggleProps) {
  const [showPrompt, setShowPrompt] = useState(false)

  const handleToggle = () => {
    if (!enabled && !showPrompt) {
      setShowPrompt(true)
    } else {
      onToggle(!enabled)
      setShowPrompt(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium">Personalization</h3>
          <p className="text-sm text-muted-foreground">
            Save your preferences to get better recommendations
          </p>
        </div>
        <Badge variant={enabled ? 'default' : 'outline'}>
          {enabled ? 'Enabled' : 'Disabled'}
        </Badge>
      </div>

      {showPrompt && (
        <div className="p-4 border rounded-lg bg-muted/50">
          <p className="text-sm mb-3">
            Enable personalization to save your search preferences? This will help us provide
            better recommendations based on your interests.
          </p>
          <div className="flex gap-2">
            <Button size="sm" onClick={() => onToggle(true)}>
              Enable
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowPrompt(false)}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {!showPrompt && (
        <Button
          variant={enabled ? 'destructive' : 'default'}
          size="sm"
          onClick={handleToggle}
        >
          {enabled ? 'Disable' : 'Enable'} Personalization
        </Button>
      )}

      {enabled && (
        <p className="text-xs text-muted-foreground">
          Your preferences are stored locally and used to boost relevant results.
        </p>
      )}
    </div>
  )
}