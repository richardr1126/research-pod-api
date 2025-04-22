import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useRef, useCallback, useEffect, useState } from 'react'
import { PodCard } from '@/components/PodCard'
import { useWebAPI } from '@/hooks/useWebAPI'
import { useDebounce } from '@uidotdev/usehooks' // Using a debounce hook

export const Route = createFileRoute('/')({
  component: App,
})

function App() {
  const { pods, loading, error, hasMore, fetchPods } = useWebAPI()
  const observer = useRef<IntersectionObserver | null>(null)
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const debouncedSearchTerm = useDebounce(searchTerm, 500) // Debounce search input by 500ms

  // Fetch initial pods or when debounced search term changes
  useEffect(() => {
    // Fetch with the debounced search term, resetting pagination (offset 0)
    fetchPods(10, 0, debouncedSearchTerm || null)
  }, [fetchPods, debouncedSearchTerm])

  const lastPodElementRef = useCallback((node: HTMLDivElement | null) => {
    if (loading) return
    if (observer.current) observer.current.disconnect()

    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        // Fetch next page using the current debounced search term
        fetchPods(10, pods.length, debouncedSearchTerm || null)
      }
    })

    if (node) observer.current.observe(node)
  }, [loading, hasMore, fetchPods, pods.length, debouncedSearchTerm])

  return (

    <div className="min-h-screen bg-base-300 p-4">

      <div className="container mx-auto">
        <div className="flex flex-col gap-6">
          {error && (
            <div className="alert alert-error">
              <span>{error}</span>
            </div>
          )}


          <label className="input w-full">
            <svg className="h-[1em] opacity-50" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
              <g
                stroke-linejoin="round"
                stroke-linecap="round"
                stroke-width="2.5"
                fill="none"
                stroke="currentColor"
              >
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.3-4.3"></path>
              </g>
            </svg>
            <input
              type="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search existing research ..."
              className="grow"
            />
          </label>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Render pods directly from the state */}
            {pods.map((pod, idx) => {
              const isLast = idx === pods.length - 1;
              return (
                <div
                  key={pod.id}
                  ref={isLast ? lastPodElementRef : undefined}
                >
                  <PodCard pod={pod} onClick={() => {
                    navigate({ to: `/pod/${pod.id}` })
                  }} />
                </div>
              );
            })}
          </div>
          {loading && (
            <div className="flex justify-center p-4">
              <span className="loading loading-spinner loading-lg"></span>
            </div>
          )}

          {!loading && !error && pods.length === 0 && (
            <div className="text-center p-8">
              <h3 className="text-lg font-semibold">No research pods found</h3>
              <p className="text-base-content/70">
                {searchTerm
                  ? `No results for "${searchTerm}". Try a different search or clear the search bar.`
                  : 'Create a new research query to get started.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
