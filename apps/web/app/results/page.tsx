'use client'

import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { useState, Suspense } from 'react'
import dynamic from 'next/dynamic'
import { searchPlaces } from '@/lib/api'
import { ResultCard } from '@/components/ResultCard'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Loader2, MapIcon, ListIcon } from 'lucide-react'

const Map = dynamic(() => import('@/components/Map'), { ssr: false })

function ResultsContent() {
  const searchParams = useSearchParams()
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list')
  const [sortBy, setSortBy] = useState<'best' | 'distance' | 'rating'>('best')

  const query = searchParams.get('query') || ''
  const lat = parseFloat(searchParams.get('lat') || '32.814')
  const lng = parseFloat(searchParams.get('lng') || '-96.948')
  const radius_m = parseInt(searchParams.get('radius_m') || '3000')
  const priceMin = searchParams.get('price_min')
  const priceMax = searchParams.get('price_max')
  const openNow = searchParams.get('open_now') === 'true'
  const multiEntityStr = searchParams.get('multi_entity')

  const { data, isLoading, error } = useQuery({
    queryKey: ['search', query, lat, lng, radius_m, priceMin, priceMax, openNow, multiEntityStr],
    queryFn: () => {
      const filters: any = {}
      if (priceMin && priceMax) {
        filters.price = [parseInt(priceMin), parseInt(priceMax)]
      }
      if (openNow) {
        filters.open_now = true
      }

      const multiEntity = multiEntityStr ? JSON.parse(multiEntityStr) : undefined

      return searchPlaces({
        query,
        lat,
        lng,
        radius_m,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        multi_entity: multiEntity,
        top_k: 30,
      })
    },
  })

  const sortedPlaces = data?.places ? [...data.places].sort((a, b) => {
    if (sortBy === 'best') return b.score - a.score
    if (sortBy === 'distance') return (a.distance_km || 0) - (b.distance_km || 0)
    if (sortBy === 'rating') return (b.rating || 0) - (a.rating || 0)
    return 0
  }) : []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded">
          <p className="font-semibold">Error loading results</p>
          <p className="text-sm">{error.toString()}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">
              {query || 'Search Results'}
            </h2>
            <p className="text-muted-foreground">
              Found {data?.places.length || 0} places
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
            >
              <ListIcon className="h-4 w-4 mr-2" />
              List
            </Button>
            <Button
              variant={viewMode === 'map' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('map')}
            >
              <MapIcon className="h-4 w-4 mr-2" />
              Map
            </Button>
          </div>
        </div>

        {/* Debug Info */}
        {data?.debug && (
          <div className="flex gap-2 flex-wrap">
            <Badge variant="secondary">
              {data.debug.agent_mode}
            </Badge>
            <Badge variant="secondary">
              {data.debug.ranking_preset}
            </Badge>
            <Badge variant={data.debug.cache_hit ? 'default' : 'outline'}>
              {data.debug.cache_hit ? 'Cached' : 'Fresh'}
            </Badge>
            <Badge variant="outline">
              {data.debug.timings.total.toFixed(2)}s
            </Badge>
          </div>
        )}

        {/* Sort Controls */}
        <div className="flex gap-2 mt-4">
          <Button
            variant={sortBy === 'best' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('best')}
          >
            Best Match
          </Button>
          <Button
            variant={sortBy === 'distance' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('distance')}
          >
            Nearest
          </Button>
          <Button
            variant={sortBy === 'rating' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('rating')}
          >
            Highest Rated
          </Button>
        </div>
      </div>

      {/* Results */}
      {viewMode === 'list' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedPlaces.map((place) => (
            <ResultCard key={place.id} place={place} />
          ))}
        </div>
      ) : (
        <div className="h-[600px] rounded-lg overflow-hidden border">
          <Map places={sortedPlaces} center={{ lat, lng }} />
        </div>
      )}

      {sortedPlaces.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No places found matching your criteria.</p>
          <Button className="mt-4" onClick={() => window.history.back()}>
            Modify Search
          </Button>
        </div>
      )}
    </div>
  )
}

export default function ResultsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <ResultsContent />
    </Suspense>
  )
}