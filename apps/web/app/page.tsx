'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import { Filters } from '@/components/Filters'
import { MultiEntityBuilder } from '@/components/MultiEntityBuilder'
import { SearchIcon } from 'lucide-react'

export default function HomePage() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState({ lat: 32.814, lng: -96.948 })
  const [radius, setRadius] = useState(3000)
  const [filters, setFilters] = useState<any>({})
  const [multiEntity, setMultiEntity] = useState<any>(null)
  const [useMultiEntity, setUseMultiEntity] = useState(false)

  const handleSearch = () => {
    const searchParams = new URLSearchParams({
      query: query || '',
      lat: location.lat.toString(),
      lng: location.lng.toString(),
      radius_m: radius.toString(),
    })

    if (filters.price) {
      searchParams.set('price_min', filters.price[0].toString())
      searchParams.set('price_max', filters.price[1].toString())
    }

    if (filters.open_now) {
      searchParams.set('open_now', 'true')
    }

    if (multiEntity && useMultiEntity) {
      searchParams.set('multi_entity', JSON.stringify(multiEntity))
    }

    router.push(`/results?${searchParams.toString()}`)
  }

  const handleUseCurrentLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition((position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        })
      })
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold mb-2">Discover Places Around You</h2>
          <p className="text-muted-foreground">
            AI-powered local discovery with multi-entity search
          </p>
        </div>

        <div className="bg-card rounded-lg border p-6 space-y-6">
          {/* Simple Query */}
          <div>
            <label className="block text-sm font-medium mb-2">
              What are you looking for?
            </label>
            <Input
              placeholder="e.g., coffee, italian restaurant, park with playground"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium mb-2">Location</label>
            <div className="flex gap-2">
              <Input
                type="number"
                placeholder="Latitude"
                value={location.lat}
                onChange={(e) =>
                  setLocation({ ...location, lat: parseFloat(e.target.value) })
                }
                step="0.000001"
              />
              <Input
                type="number"
                placeholder="Longitude"
                value={location.lng}
                onChange={(e) =>
                  setLocation({ ...location, lng: parseFloat(e.target.value) })
                }
                step="0.000001"
              />
              <Button onClick={handleUseCurrentLocation} variant="outline">
                Use Current
              </Button>
            </div>
          </div>

          {/* Radius */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Search Radius: {(radius / 1000).toFixed(1)} km
            </label>
            <Slider
              value={[radius]}
              onValueChange={(values) => setRadius(values[0])}
              min={500}
              max={50000}
              step={500}
            />
          </div>

          {/* Filters */}
          <Filters filters={filters} onChange={setFilters} />

          {/* Multi-Entity Builder */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium">
                Advanced: Multi-Entity Search
              </label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setUseMultiEntity(!useMultiEntity)}
              >
                {useMultiEntity ? 'Disable' : 'Enable'}
              </Button>
            </div>
            {useMultiEntity && (
              <MultiEntityBuilder
                value={multiEntity}
                onChange={setMultiEntity}
              />
            )}
          </div>

          {/* Search Button */}
          <Button onClick={handleSearch} className="w-full" size="lg">
            <SearchIcon className="mr-2 h-5 w-5" />
            Search
          </Button>
        </div>

        {/* Examples */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-4">Try these examples:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Button
              variant="outline"
              className="justify-start"
              onClick={() => setQuery('coffee near me')}
            >
              Coffee near me
            </Button>
            <Button
              variant="outline"
              className="justify-start"
              onClick={() => setQuery('italian restaurant under $$$')}
            >
              Italian restaurant under $$$
            </Button>
            <Button
              variant="outline"
              className="justify-start"
              onClick={() => {
                setQuery('family-friendly restaurant near park with playground')
                setUseMultiEntity(true)
              }}
            >
              Restaurant near park with playground
            </Button>
            <Button
              variant="outline"
              className="justify-start"
              onClick={() => setQuery('cinema with recliners')}
            >
              Cinema with recliners
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}