'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, MapPin, Search } from 'lucide-react'

export default function Home() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [lat, setLat] = useState('')
  const [lng, setLng] = useState('')
  const [loading, setLoading] = useState(false)
  const [gettingLocation, setGettingLocation] = useState(false)

  const getCurrentLocation = () => {
    setGettingLocation(true)
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLat(position.coords.latitude.toString())
          setLng(position.coords.longitude.toString())
          setGettingLocation(false)
        },
        (error) => {
          console.error('Error getting location:', error)
          setGettingLocation(false)
          alert('Could not get your location. Please enter it manually.')
        }
      )
    } else {
      setGettingLocation(false)
      alert('Geolocation is not supported by your browser.')
    }
  }

  const handleSearch = () => {
    if (!query.trim()) {
      alert('Please enter a search query')
      return
    }
    if (!lat || !lng) {
      alert('Please provide your location')
      return
    }

    setLoading(true)

    const params = new URLSearchParams({
      query: query.trim(),
      lat,
      lng,
    })

    router.push(`/results?${params.toString()}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Around Me
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              Discover amazing places around you with natural language
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Just describe what you're looking for, and let AI do the rest
            </p>
          </div>

          {/* Search Card */}
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle>What are you looking for?</CardTitle>
              <CardDescription>
                Describe what you want in natural language - no filters needed!
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Query Input */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Your Search
                </label>
                <Textarea
                  placeholder="E.g., 'quiet coffee shop near me where I can study' or 'affordable italian restaurant open now within 2 miles' or 'family-friendly restaurant near a park with playground'"
                  value={query}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setQuery(e.target.value)}
                  className="min-h-24 resize-none"
                  onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSearch()
                    }
                  }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Press Enter to search, Shift+Enter for new line
                </p>
              </div>

              {/* Location */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Your Location
                </label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={getCurrentLocation}
                    disabled={gettingLocation}
                    className="w-fit"
                  >
                    {gettingLocation ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <MapPin className="h-4 w-4 mr-2" />
                    )}
                    Use Current Location
                  </Button>
                  <div className="flex-1 flex gap-2">
                    <Input
                      placeholder="Latitude"
                      value={lat}
                      onChange={(e) => setLat(e.target.value)}
                      type="number"
                      step="any"
                    />
                    <Input
                      placeholder="Longitude"
                      value={lng}
                      onChange={(e) => setLng(e.target.value)}
                      type="number"
                      step="any"
                    />
                  </div>
                </div>
              </div>

              {/* Search Button */}
              <Button
                onClick={handleSearch}
                disabled={loading || !query.trim() || !lat || !lng}
                className="w-full"
                size="lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-5 w-5" />
                    Search
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Example Queries */}
          <div className="mt-8">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Try these examples:
            </p>
            <div className="grid gap-2">
              {[
                'coffee shop with wifi and outdoor seating',
                'cheap mexican food open now',
                'family restaurant near playground within walking distance',
                'quiet place to work with good coffee under $15',
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => setQuery(example)}
                  className="text-left text-sm p-3 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  "{example}"
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}