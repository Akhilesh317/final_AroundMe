'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Input } from './ui/input'

interface FiltersProps {
  filters: any
  onChange: (filters: any) => void
}

export function Filters({ filters, onChange }: FiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  const toggleOpenNow = () => {
    onChange({
      ...filters,
      open_now: !filters.open_now,
    })
  }

  const setPriceRange = (min: number, max: number) => {
    onChange({
      ...filters,
      price: [min, max],
    })
  }

  const clearFilters = () => {
    onChange({})
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">Filters</label>
        {Object.keys(filters).length > 0 && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            Clear All
          </Button>
        )}
      </div>

      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2">
        <Badge
          variant={filters.open_now ? 'default' : 'outline'}
          className="cursor-pointer"
          onClick={toggleOpenNow}
        >
          Open Now
        </Badge>

        <Badge
          variant={filters.price?.[0] === 1 && filters.price?.[1] === 1 ? 'default' : 'outline'}
          className="cursor-pointer"
          onClick={() => setPriceRange(1, 1)}
        >
          $
        </Badge>

        <Badge
          variant={filters.price?.[0] === 1 && filters.price?.[1] === 2 ? 'default' : 'outline'}
          className="cursor-pointer"
          onClick={() => setPriceRange(1, 2)}
        >
          $ - $$
        </Badge>

        <Badge
          variant={filters.price?.[0] === 1 && filters.price?.[1] === 3 ? 'default' : 'outline'}
          className="cursor-pointer"
          onClick={() => setPriceRange(1, 3)}
        >
          $ - $$$
        </Badge>

        <Badge
          variant={filters.price?.[0] === 3 && filters.price?.[1] === 4 ? 'default' : 'outline'}
          className="cursor-pointer"
          onClick={() => setPriceRange(3, 4)}
        >
          $$$ - $$$$
        </Badge>
      </div>

      {/* Advanced Filters */}
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? 'Hide' : 'Show'} Advanced Filters
        </Button>

        {showAdvanced && (
          <div className="mt-3 space-y-3 p-4 border rounded-lg">
            <div>
              <label className="block text-sm font-medium mb-2">Category</label>
              <Input
                placeholder="e.g., cafe, restaurant, park"
                value={filters.category || ''}
                onChange={(e) =>
                  onChange({ ...filters, category: e.target.value })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Min Price
                </label>
                <select
                  className="w-full h-10 rounded-md border border-input bg-background px-3 py-2"
                  value={filters.price?.[0] || 0}
                  onChange={(e) =>
                    setPriceRange(
                      parseInt(e.target.value),
                      filters.price?.[1] || 4
                    )
                  }
                >
                  <option value={0}>Any</option>
                  <option value={1}>$ (Cheap)</option>
                  <option value={2}>$$ (Moderate)</option>
                  <option value={3}>$$$ (Expensive)</option>
                  <option value={4}>$$$$ (Very Expensive)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Max Price
                </label>
                <select
                  className="w-full h-10 rounded-md border border-input bg-background px-3 py-2"
                  value={filters.price?.[1] || 4}
                  onChange={(e) =>
                    setPriceRange(
                      filters.price?.[0] || 0,
                      parseInt(e.target.value)
                    )
                  }
                >
                  <option value={1}>$ (Cheap)</option>
                  <option value={2}>$$ (Moderate)</option>
                  <option value={3}>$$$ (Expensive)</option>
                  <option value={4}>$$$$ (Very Expensive)</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}