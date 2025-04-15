import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useRef, useCallback, useEffect } from 'react'
import { PodCard } from '@/components/PodCard'
import { useWebAPI } from '@/hooks/useWebAPI'
import { useState} from 'react'

export const Route = createFileRoute('/')({
  component: App,
})

function App() {
  const { pods, loading, error, hasMore, fetchPods } = useWebAPI()
  const observer = useRef<IntersectionObserver | null>(null)
  const navigate = useNavigate() 
  const [search, setSearch] = useState('')
  const filteredPods = pods.filter(pod =>
    pod.query.toLowerCase().includes(search.toLowerCase()))
    
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

      <div className="mb-6">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search podcasts..."
          className="input input-bordered w-full"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {pods
          .filter(pod =>
            pod.query.toLowerCase().includes(search.toLowerCase())
          )
          .map(pod => (
            <PodCard key={pod.id} pod={pod} onClick={() => {navigate({ to: `/pod/${pod.id}` }) 
            }} />
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
