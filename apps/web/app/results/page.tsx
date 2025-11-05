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
import { Card, CardContent } from '@/components/ui/card'
import { Loader2, MapIcon, ListIcon, Send, User, Bot, X, BarChart3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { QuickStats } from '@/components/visualizations/QuickStats'
import { PriceDistribution } from '@/components/visualizations/PriceDistribution'
import { RatingDistribution } from '@/components/visualizations/RatingDistribution'
import { DistanceVisualization } from '@/components/visualizations/DistanceVisualization'
import { CategoryBreakdown } from '@/components/visualizations/CategoryBreakdown'
import { ScoreBreakdown } from '@/components/visualizations/ScoreBreakdown'
import { FeatureHeatmap } from '@/components/visualizations/FeatureHeatmap'

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
  const [showViz, setShowViz] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const query = searchParams.get('query') || ''
  const originalQuery = searchParams.get('original_query') || query
  const lat = parseFloat(searchParams.get('lat') || '32.814')
  const lng = parseFloat(searchParams.get('lng') || '-96.948')
  const radius_m = parseInt(searchParams.get('radius_m') || '3000')
  const priceMin = searchParams.get('price_min')
  const priceMax = searchParams.get('price_max')
  const openNow = searchParams.get('open_now') === 'true'
  const multiEntityStr = searchParams.get('multi_entity')
  const isFollowup = searchParams.get('is_followup') === 'true'
  const resultSetId = searchParams.get('result_set_id')

  // Fetch data
  const { data, isLoading, error } = useQuery({
    queryKey: ['search', query, lat, lng, radius_m, priceMin, priceMax, openNow, multiEntityStr, isFollowup, resultSetId],
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
        context: isFollowup ? {
          follow_up: true,
          result_set_id: resultSetId || undefined,
          original_query: originalQuery
        } : undefined,
      })
    },
  })

  // Add initial query to messages
  useEffect(() => {
    if (query && messages.length === 0 && data?.places) {
      const isRefinement = isFollowup && originalQuery !== query
      
      setMessages([
        {
          role: 'user',
          content: isRefinement ? query : originalQuery,
          timestamp: new Date(),
        },
        {
          role: 'assistant',
          content: isRefinement 
            ? `I filtered the results based on "${query}". Found ${data.places.length} matching places!`
            : `I found ${data.places.length} places matching "${query}". You can refine your search by asking me to filter by price, distance, ratings, or specific features!`,
          timestamp: new Date(),
        },
      ])
    }
  }, [query, data, messages.length, isFollowup, originalQuery])

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 🤖 AI-POWERED FOLLOW-UP HANDLER
  const handleSendMessage = () => {
    if (!chatMessage.trim()) return

    const userInput = chatMessage.trim()

    // Add user message to chat
    const userMessage: Message = {
      role: 'user',
      content: userInput,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Build search parameters for follow-up
    const params = new URLSearchParams({
      query: userInput,
      lat: lat.toString(),
      lng: lng.toString(),
      radius_m: radius_m.toString(),
      original_query: originalQuery,
      is_followup: 'true',
      result_set_id: data?.result_set_id || '',
    })

    setChatMessage('')
    router.push(`/results?${params.toString()}`)
  }

  // Handle quick refinement buttons
  const handleQuickRefinement = (refinement: string) => {
    setChatMessage(refinement)
    setTimeout(() => {
      if (refinement.trim()) {
        const userMessage: Message = {
          role: 'user',
          content: refinement,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, userMessage])

        const params = new URLSearchParams({
          query: refinement,
          lat: lat.toString(),
          lng: lng.toString(),
          radius_m: radius_m.toString(),
          original_query: originalQuery,
          is_followup: 'true',
          result_set_id: data?.result_set_id || '',
        })

        setChatMessage('')
        router.push(`/results?${params.toString()}`)
      }
    }, 100)
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
                <h3 className="font-semibold">AI Assistant</h3>
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
              {messages.length === 0 && (
                <div className="text-center text-muted-foreground text-sm py-8">
                  <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Ask me to refine your search!</p>
                  <p className="text-xs mt-1">I use AI to understand your requests 🤖</p>
                </div>
              )}
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
              <p className="text-xs text-muted-foreground mb-2">🤖 AI-powered refinements:</p>
              <div className="flex flex-wrap gap-1">
                {[
                  'cheaper options',
                  'within 2 km',
                  'with wifi',
                  'highly rated',
                  'family friendly',
                  'outdoor seating',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleQuickRefinement(suggestion)}
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
                  placeholder="Ask me anything..."
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
              <p className="text-xs text-muted-foreground mt-2">
                💡 Try: "cheaper", "within 3 miles", "with parking"
              </p>
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
                  Found {sortedPlaces.length} places
                  {originalQuery && <span className="ml-1">for "{originalQuery}"</span>}
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
                  {data.debug.cache_hit ? '🔥 Filtered' : 'Fresh'}
                </Badge>
                <Badge variant="outline">{data.debug.timings.total.toFixed(2)}s</Badge>
                {data.debug.counts_before_after && (
                  <Badge variant="outline">
                    {data.debug.counts_before_after.original} → {data.debug.counts_before_after.filtered}
                  </Badge>
                )}
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

          {/* 📊 VISUALIZATIONS SECTION */}
          {sortedPlaces.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Insights & Analytics
                </h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowViz(!showViz)}
                >
                  {showViz ? 'Hide' : 'Show'} Charts
                </Button>
              </div>

              {showViz && (
                <div className="space-y-6">
                  {/* Quick Stats */}
                  <QuickStats places={sortedPlaces} />

                  {/* Charts Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Row 1: Price & Rating */}
                    <Card>
                      <CardContent className="p-4">
                        <PriceDistribution places={sortedPlaces} />
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-4">
                        <RatingDistribution places={sortedPlaces} />
                      </CardContent>
                    </Card>

                    {/* Row 2: Category & Score */}
                    <Card>
                      <CardContent className="p-4">
                        <CategoryBreakdown places={sortedPlaces} />
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-4">
                        <ScoreBreakdown places={sortedPlaces} />
                      </CardContent>
                    </Card>

                    {/* Row 3: Distance Scatter */}
                    <Card className="lg:col-span-2">
                      <CardContent className="p-4">
                        <DistanceVisualization places={sortedPlaces} />
                      </CardContent>
                    </Card>

                    {/* Row 4: Feature Heatmap */}
                    <Card className="lg:col-span-2">
                      <CardContent className="p-4">
                        <FeatureHeatmap 
                          places={sortedPlaces} 
                          featureAnalysis={data?.debug?.feature_analysis}
                        />
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </div>
          )}

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
              <Button className="mt-4" onClick={() => router.push('/')}>
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

