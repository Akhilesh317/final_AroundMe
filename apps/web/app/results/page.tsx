'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { useState, Suspense, useRef, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { searchPlaces } from '@/lib/api'
import { ResultCard } from '@/components/ResultCard'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Loader2, MapIcon, ListIcon, Send, User, Bot, X } from 'lucide-react'
import { cn } from '@/lib/utils'

const Map = dynamic(() => import('@/components/Map'), { ssr: false })

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function ResultsContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list')
  const [sortBy, setSortBy] = useState<'best' | 'distance' | 'rating'>('best')
  const [chatMessage, setChatMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [chatOpen, setChatOpen] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const query = searchParams.get('query') || ''
  const lat = parseFloat(searchParams.get('lat') || '32.814')
  const lng = parseFloat(searchParams.get('lng') || '-96.948')
  const radius_m = parseInt(searchParams.get('radius_m') || '3000')
  const priceMin = searchParams.get('price_min')
  const priceMax = searchParams.get('price_max')
  const openNow = searchParams.get('open_now') === 'true'
  const multiEntityStr = searchParams.get('multi_entity')

  // Fetch data FIRST
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

  // Add initial query to messages (after data is available)
  useEffect(() => {
    if (query && messages.length === 0 && data?.places) {
      setMessages([
        {
          role: 'user',
          content: query,
          timestamp: new Date(),
        },
        {
          role: 'assistant',
          content: `I found ${data.places.length} places matching "${query}". You can refine your search by asking me to filter by price, distance, ratings, or specific features!`,
          timestamp: new Date(),
        },
      ])
    }
  }, [query, data, messages.length])

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = () => {
    if (!chatMessage.trim()) return

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: chatMessage.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Navigate with new query
    const params = new URLSearchParams({
      query: chatMessage.trim(),
      lat: lat.toString(),
      lng: lng.toString(),
      radius_m: radius_m.toString(),
    })

    // Add conversation context
    if (data?.result_set_id) {
      params.append('result_set_id', data.result_set_id)
      params.append('follow_up', 'true')
    }

    setChatMessage('')
    router.push(`/results?${params.toString()}`)
  }

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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Sidebar */}
        <div className={cn(
          "lg:col-span-1 order-1 lg:order-1",
          !chatOpen && "hidden lg:block"
        )}>
          <Card className="sticky top-4 flex flex-col h-[calc(100vh-8rem)]">
            {/* Chat Header */}
            <div className="p-4 border-b flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-primary" />
                <h3 className="font-semibold">Search Assistant</h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setChatOpen(false)}
                className="lg:hidden"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={cn(
                    "flex gap-3",
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "rounded-lg px-4 py-2 max-w-[80%]",
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary'
                    )}
                  >
                    <p className="text-sm">{message.content}</p>
                    <span className="text-xs opacity-70 mt-1 block">
                      {message.timestamp.toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                      <User className="h-4 w-4 text-primary-foreground" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Suggested Refinements */}
            <div className="p-3 border-t bg-secondary/30">
              <p className="text-xs text-muted-foreground mb-2">Quick refinements:</p>
              <div className="flex flex-wrap gap-1">
                {[
                  'cheaper options',
                  'within 1 mile',
                  'with wifi',
                  'open now',
                  'top rated',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setChatMessage(suggestion)}
                    className="text-xs px-2 py-1 rounded-md bg-secondary hover:bg-secondary/80 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Input */}
            <div className="p-4 border-t">
              <div className="flex gap-2">
                <Input
                  placeholder="Refine your search..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSendMessage()
                    }
                  }}
                  className="flex-1"
                />
                <Button onClick={handleSendMessage} disabled={!chatMessage.trim()} size="icon">
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-2 order-2 lg:order-2">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold">Search Results</h2>
                <p className="text-muted-foreground">
                  Found {data?.places.length || 0} places
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setChatOpen(true)}
                  className="lg:hidden"
                >
                  <Bot className="h-4 w-4 mr-2" />
                  Chat
                </Button>
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
              <div className="flex gap-2 flex-wrap mb-4">
                <Badge variant="secondary">{data.debug.agent_mode}</Badge>
                <Badge variant="secondary">{data.debug.ranking_preset}</Badge>
                <Badge variant={data.debug.cache_hit ? 'default' : 'outline'}>
                  {data.debug.cache_hit ? 'Cached' : 'Fresh'}
                </Badge>
                <Badge variant="outline">{data.debug.timings.total.toFixed(2)}s</Badge>
              </div>
            )}

            {/* Sort Controls */}
            <div className="flex gap-2">
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                New Search
              </Button>
            </div>
          )}
        </div>
      </div>
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