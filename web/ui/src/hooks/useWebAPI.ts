import { useState, useEffect, useCallback, useRef } from 'react'

const API_BASE = 'https://api.richardr.dev'

export type ResearchPodStatus = 'QUEUED' | 'ASSIGNED' | 'PROCESSING' | 'IN_PROGRESS' | 'COMPLETED' | 'ERROR'

export interface Pod {
  id: string
  query: string
  title: string
  audio_url: string | null
  keywords_arxiv: string[][] | null
  sources_arxiv: Array<{ title: string; url: string; authors: string | string[] }> | null
  sources_ddg: Array<{ title: string; url: string; snippet?: string; keywords_used?: string[] }> | null
  transcript: string | null
  status: ResearchPodStatus
  error_message: string | null
  consumer_id: string
  created_at: number
  updated_at: number
  similar_pods: Pod[] | null
}

interface ResearchPodEventData {
  status?: ResearchPodStatus
  progress?: number
  message?: string
  papers?: string[]
  key_findings?: string
}

export function useWebAPI() {
  // Pod list state
  const [pods, setPods] = useState<Pod[]>([])
  const [loading, setLoading] = useState(true)
  const [hasMore, setHasMore] = useState(true)

  // Research pod state
  const [podId, setPodId] = useState<string | null>(null)
  const [status, setStatus] = useState<ResearchPodStatus | null>(null)
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState<string | null>(null)
  const [eventsUrl, setEventsUrl] = useState<string | null>(null)
  const [podDetails, setPodDetails] = useState<Pod | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // References for cleanup
  const eventSourceRef = useRef<EventSource | null>(null)
  const pollingIntervalRef = useRef<number | null>(null)

  // Pod list methods
  const fetchPods = useCallback(async (limit = 10, offset = 0) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/v1/api/pods?limit=${limit}&offset=${offset}`)
      if (!response.ok) throw new Error('Failed to fetch pods')
      const data = await response.json()
      setPods(prev => offset === 0 ? data : [...prev, ...data])
      setHasMore(data.length === limit)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchPodById = useCallback(async (id: string): Promise<Pod> => {
    try {
      const response = await fetch(`${API_BASE}/v1/api/pod/get/${id}`)
      if (!response.ok) throw new Error('Failed to fetch pod details')
      return await response.json()
    } catch (err) {
      throw err
    }
  }, [])

  // Research pod methods
  const reset = useCallback(() => {
    setPodId(null)
    setStatus(null)
    setProgress(0)
    setMessage(null)
    setEventsUrl(null)
    setPodDetails(null)
    setError(null)
    setIsLoading(false)
    // Clear any existing event source and polling interval
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }, [])

  const createPod = useCallback(async (query: string) => {
    try {
      reset()
      setIsLoading(true)
      const response = await fetch(`${API_BASE}/v1/api/pod/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to create research pod')
      }
      
      setPodId(data.pod_id)
      setEventsUrl(data.events_url)
      setStatus('QUEUED')
      setProgress(0)
      setMessage('Starting research pod...')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create research pod')
    } finally {
      setIsLoading(false)
    }
  }, [reset])

  const fetchStatus = useCallback(async () => {
    if (!podId) return

    try {
      const response = await fetch(`${API_BASE}/v1/api/pod/status/${podId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch status')
      }
      const data = await response.json()
      setStatus(data.status)
      setProgress(data.progress)
      setMessage(data.message)
      setEventsUrl(data.events_url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status')
    }
  }, [podId])

  const fetchDetails = useCallback(async () => {
    if (!podId) return

    try {
      const response = await fetch(`${API_BASE}/v1/api/pod/get/${podId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch pod details')
      }
      const data = await response.json()
      setPodDetails(data)
    } catch (err) {
      console.error('Error fetching pod details:', err)
      setError(err instanceof Error ? err.message : 'Failed to pod details')
    }
  }, [podId])

  // Event stream effect with improved cleanup
  useEffect(() => {
    if (!podId) return

    const connectToEventStream = (url: string) => {
      if (!url || eventSourceRef.current) return

      const es = new EventSource(url)
      eventSourceRef.current = es
      
      es.onmessage = (event: MessageEvent<string>) => {
        try {
          const data: ResearchPodEventData = JSON.parse(event.data)
          if (data.status) setStatus(data.status)
          if (typeof data.progress === 'number') setProgress(data.progress)
          if (data.message) setMessage(data.message)

          if (data.status === 'COMPLETED' || data.status === 'ERROR') {
            es.close()
            eventSourceRef.current = null
            fetchDetails()
          }
        } catch (err) {
          console.error('Error parsing event data:', err)
        }
      }

      es.onerror = () => {
        es.close()
        eventSourceRef.current = null
        // Attempt to reconnect unless we're done
        if (status !== 'COMPLETED' && status !== 'ERROR') {
          setTimeout(() => connectToEventStream(url), 5000)
        }
      }
    }

    // Clear any existing connections before starting new ones
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }

    if (!eventsUrl) {
      // Poll for status until we get an events_url
      pollingIntervalRef.current = window.setInterval(fetchStatus, 2000)
    } else {
      connectToEventStream(eventsUrl)
    }

    // Cleanup function
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [podId, eventsUrl, status, fetchStatus, fetchDetails])

  return {
    // Pod list
    pods,
    loading,
    error,
    hasMore,
    fetchPods,

    // Research pod
    createPod,
    fetchPodById,
    status,
    progress,
    message,
    podDetails,
    isLoading,
    reset
  }
}