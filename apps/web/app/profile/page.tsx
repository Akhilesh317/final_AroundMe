'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PreferenceToggle } from '@/components/PreferenceToggle'
import { getPreferences, updatePreferences, deletePreferences } from '@/lib/api'
import { PlusIcon, XIcon, Loader2 } from 'lucide-react'

export default function ProfilePage() {
  const [userId] = useState('demo_user') // In production, get from auth
  const [personalizationEnabled, setPersonalizationEnabled] = useState(false)
  const [newPrefKey, setNewPrefKey] = useState('')
  const [newPrefValue, setNewPrefValue] = useState('')
  const [newPrefWeight, setNewPrefWeight] = useState(0.5)

  const queryClient = useQueryClient()

  const { data: preferencesData, isLoading } = useQuery({
    queryKey: ['preferences', userId],
    queryFn: () => getPreferences(userId),
    enabled: personalizationEnabled,
  })

  const updateMutation = useMutation({
    mutationFn: (preferences: any[]) => updatePreferences(userId, preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences', userId] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deletePreferences(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences', userId] })
    },
  })

  const preferences = preferencesData?.preferences || []

  const handleAddPreference = () => {
    if (!newPrefKey || !newPrefValue) return

    const newPrefs = [
      ...preferences.map((p: any) => ({
        key: p.key,
        value: p.value,
        weight: p.weight,
      })),
      {
        key: newPrefKey,
        value: newPrefValue,
        weight: newPrefWeight,
      },
    ]

    updateMutation.mutate(newPrefs)
    setNewPrefKey('')
    setNewPrefValue('')
    setNewPrefWeight(0.5)
  }

  const handleRemovePreference = (index: number) => {
    const newPrefs = preferences
      .filter((_: any, i: number) => i !== index)
      .map((p: any) => ({
        key: p.key,
        value: p.value,
        weight: p.weight,
      }))

    updateMutation.mutate(newPrefs)
  }

  const handleClearAll = () => {
    if (confirm('Are you sure you want to delete all preferences?')) {
      deleteMutation.mutate()
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Profile & Preferences</h1>
        <p className="text-muted-foreground mb-8">
          Manage your personalization settings and search preferences
        </p>

        {/* Personalization Toggle */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Personalization Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <PreferenceToggle
              enabled={personalizationEnabled}
              onToggle={setPersonalizationEnabled}
            />
          </CardContent>
        </Card>

        {/* Preferences Management */}
        {personalizationEnabled && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Your Preferences</CardTitle>
                {preferences.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClearAll}
                    disabled={deleteMutation.isPending}
                  >
                    Clear All
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <>
                  {/* Existing Preferences */}
                  {preferences.length > 0 ? (
                    <div className="space-y-3">
                      {preferences.map((pref: any, index: number) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 border rounded-lg"
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="secondary">{pref.key}</Badge>
                              <span className="text-sm font-medium">{pref.value}</span>
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Weight: {pref.weight.toFixed(2)}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemovePreference(index)}
                            disabled={updateMutation.isPending}
                          >
                            <XIcon className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground py-8">
                      No preferences saved yet. Add your first preference below.
                    </p>
                  )}

                  {/* Add New Preference */}
                  <div className="border-t pt-6">
                    <h4 className="font-medium mb-3">Add New Preference</h4>
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-sm font-medium mb-1 block">Key</label>
                          <Input
                            placeholder="e.g., category, cuisine"
                            value={newPrefKey}
                            onChange={(e) => setNewPrefKey(e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-1 block">Value</label>
                          <Input
                            placeholder="e.g., italian, cafe"
                            value={newPrefValue}
                            onChange={(e) => setNewPrefValue(e.target.value)}
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-sm font-medium mb-1 block">
                          Weight: {newPrefWeight.toFixed(2)}
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={newPrefWeight}
                          onChange={(e) => setNewPrefWeight(parseFloat(e.target.value))}
                          className="w-full"
                        />
                      </div>

                      <Button
                        onClick={handleAddPreference}
                        disabled={!newPrefKey || !newPrefValue || updateMutation.isPending}
                        className="w-full"
                      >
                        <PlusIcon className="h-4 w-4 mr-2" />
                        Add Preference
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {/* Info Section */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>How Personalization Works</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>
              • Preferences boost relevant places in search results by up to 15%
            </p>
            <p>
              • Higher weight values (0.8-1.0) have stronger influence
            </p>
            <p>
              • Common preference keys: category, cuisine, feat_* (features)
            </p>
            <p>
              • Your data is stored securely and never shared
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}