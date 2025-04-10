import { createFileRoute } from '@tanstack/react-router'
import { useRef, useCallback, useEffect } from 'react'
import { PodCard } from '@/components/PodCard'
import { useWebAPI } from '@/hooks/useWebAPI'

export const Route = createFileRoute('/')({
  component: App,
})

function App() {
  const { pods, loading, error, hasMore, fetchPods } = useWebAPI()
  const observer = useRef<IntersectionObserver | null>(null)
  
  // Initial fetch
  useEffect(() => {
    fetchPods(10, 0)
  }, [fetchPods])
  
  const lastPodElementRef = useCallback((node: HTMLDivElement | null) => {
    if (loading) return
    if (observer.current) observer.current.disconnect()
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        fetchPods(10, pods.length)
      }
    })
    
    if (node) observer.current.observe(node)
  }, [loading, hasMore, fetchPods, pods.length])

  return (
    <div className="min-h-screen bg-base-300 p-4">
      <div className="container mx-auto">
        <div className="flex flex-col gap-6">
          {error && (
            <div className="alert alert-error">
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pods.map((pod, index) => (
              <div
                key={pod.id}
                ref={index === pods.length - 1 ? lastPodElementRef : undefined}
              >
                <PodCard
                  pod={pod}
                  onClick={() => {
                    // TODO: Navigate to pod details page
                    console.log('Navigate to pod:', pod.id)
                  }}
                />
              </div>
            ))}
          </div>

          {loading && (
            <div className="flex justify-center p-4">
              <span className="loading loading-spinner loading-lg"></span>
            </div>
          )}

          {!loading && !error && pods.length === 0 && (
            <div className="text-center p-8">
              <h3 className="text-lg font-semibold">No research pods found</h3>
              <p className="text-base-content/70">Create a new research query to get started.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
