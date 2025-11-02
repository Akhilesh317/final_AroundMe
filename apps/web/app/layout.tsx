import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Around Me - Local Discovery',
  description: 'Discover amazing places around you with AI-powered search',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen flex flex-col">
            <header className="border-b">
              <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between">
                  <h1 className="text-2xl font-bold">Around Me</h1>
                  <nav className="flex gap-4">
                    <a href="/" className="hover:text-primary">Search</a>
                    <a href="/profile" className="hover:text-primary">Profile</a>
                    <a href="/admin" className="hover:text-primary">Admin</a>
                  </nav>
                </div>
              </div>
            </header>
            <main className="flex-1">
              {children}
            </main>
            <footer className="border-t py-6">
              <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
                <p>Powered by Google Places API and Yelp Fusion API</p>
                <p className="mt-2">
                  Data from{' '}
                  <a href="https://developers.google.com/maps" className="underline" target="_blank" rel="noopener noreferrer">
                    Google Maps Platform
                  </a>
                  {' '}and{' '}
                  <a href="https://www.yelp.com/developers" className="underline" target="_blank" rel="noopener noreferrer">
                    Yelp
                  </a>
                </p>
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  )
}