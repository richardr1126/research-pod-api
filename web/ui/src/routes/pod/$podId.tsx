import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { useWebAPI } from '@/hooks/useWebAPI'
import type { Pod } from '@/hooks/useWebAPI'
import { PodDetails } from '@/components/PodDetails'

export const Route = createFileRoute('/pod/$podId')({
  component: PodDetailsPage,
})

function PodDetailsPage() {
  const { podId } = Route.useParams() 
  const { fetchPodById } = useWebAPI()
  const [pod, setPod] = useState<Pod | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!podId) return
    setLoading(true)
    fetchPodById(podId)
      .then(setPod)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load pod details')
      )
      .finally(() => setLoading(false))
  }, [podId, fetchPodById])

  if (loading) return <div className="p-6 text-center">Loading...</div>
  if (error) return <div className="p-6 text-center text-red-500">{error}</div>
  if (!pod) return <div className="p-6 text-center">Pod not found.</div>

  return <PodDetails pod={pod} />
}
