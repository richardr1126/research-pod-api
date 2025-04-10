import { createFileRoute } from '@tanstack/react-router'
import { useState, useRef, useEffect } from 'react'
import { useWebAPI } from '../hooks/useWebAPI'
import { PodCard } from '../components/PodCard'
import { SourceTag } from '../components/SourceTag'

export const Route = createFileRoute('/create')({
  component: CreatePage,
})

function CreatePage() {
  const [query, setQuery] = useState('')
  const [messageHistory, setMessageHistory] = useState<Array<{ text: string, timestamp: number }>>([])
  const eventsRef = useRef<HTMLDivElement>(null)
  const {
    createPod,
    status,
    progress,
    message,
    error,
    podDetails,
    isLoading,
    reset
  } = useWebAPI()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    // Clear message history before creating new pod
    setMessageHistory([])
    await createPod(query.trim())
  }

  // Update message history when new message arrives
  useEffect(() => {
    if (message) {
      setMessageHistory(prev => [...prev, {
        text: message,
        timestamp: Math.floor(Date.now() / 1000) // Store as UTC seconds
      }])
    }
  }, [message])

  // Update this useEffect to also clear message history on reset
  useEffect(() => {
    if (podDetails) {
      setMessageHistory([])
    }
  }, [podDetails])

  // Scroll to bottom when messages update
  useEffect(() => {
    if (eventsRef.current) {
      eventsRef.current.scrollTop = eventsRef.current.scrollHeight
    }
  }, [messageHistory])

  return (
    <div className="min-h-screen bg-base-300 mx-auto p-4 lg:p-8">
      <div className="space-y-4">
        {/* Create Form */}
        <div className="card bg-base-100">
          <div className="card-body">
            <h2 className="card-title">Create Research Pod</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="form-control w-full">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your research query..."
                  className="input input-bordered w-full"
                  disabled={isLoading || !!podDetails}
                />
              </div>
              <div className="flex gap-4">
                <button
                  type="submit"
                  disabled={isLoading || !query.trim() || !!podDetails}
                  className="btn btn-primary"
                >
                  {isLoading ? 'Creating...' : 'Create Pod'}
                </button>
                {podDetails && (
                  <button
                    type="button"
                    onClick={reset}
                    className="btn btn-secondary"
                  >
                    Create Another
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>

        {/* Status Section */}
        {(status || error) && (
          <div className="card bg-base-100">
            <div className="card-body">
              <h2 className="card-title">Status</h2>
              {error ? (
                <div className="alert alert-error">{error}</div>
              ) : (
                <div className="space-y-2">
                  <progress
                    className="progress progress-primary w-full"
                    value={progress}
                    max="100"
                  />
                  <div className="flex justify-between text-sm opacity-70">
                    <span>{status}</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="text-base-content">{message}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Events Log */}
        {messageHistory.length > 0 && (
          <div className="card bg-base-100">
            <div className="card-body">
              <h2 className="card-title flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                </svg>
                Activity Log
              </h2>
              <div
                ref={eventsRef}
                className="h-[300px] overflow-y-auto space-y-2 bg-base-300 rounded-box p-2"
              >
                {messageHistory.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 py-1 px-2 rounded-lg transition-all duration-200 ${
                      index === messageHistory.length - 1 ? 'bg-primary bg-opacity-10' : 'bg-base-100'
                    }`}
                  >
                    <div className="flex-none">
                      {msg.text.toLowerCase().includes('error') ? (
                        <div className="w-2 h-2 mt-2 rounded-full bg-error"></div>
                      ) : msg.text.toLowerCase().includes('complete') ? (
                        <div className="w-2 h-2 mt-2 rounded-full bg-success"></div>
                      ) : (
                        <div className="w-2 h-2 mt-2 rounded-full bg-primary"></div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm opacity-70">
                        {new Date(msg.timestamp * 1000).toLocaleTimeString()}
                      </div>
                      <div className="text-base-content">{msg.text}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Pod Details */}
        {podDetails && (
          <div className="card bg-base-100">
            <div className="card-body">
              <h2 className="card-title">Research Results</h2>

              {/* Keywords */}
              {podDetails.keywords_arxiv && podDetails.keywords_arxiv.length > 0 && (
                <div className="flex flex-wrap gap-2 my-2">
                  {podDetails.keywords_arxiv.map((group, i) => (
                    <div key={i} className="flex flex-wrap gap-2">
                      {group.map((keyword, j) => (
                        <span
                          key={`${i}-${j}`}
                          className="badge badge-primary"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  ))}
                </div>
              )}

              {/* Audio Player */}
              {podDetails.audio_url && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium mb-2">Podcast</h3>
                  <audio controls className="w-full">
                    <source src={podDetails.audio_url} type="audio/mpeg" />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}

              {/* Transcript */}
              {podDetails.transcript && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium mb-2">Transcript</h3>
                  <div className="prose max-w-none">
                    {podDetails.transcript}
                  </div>
                </div>
              )}

              {/* Sources */}
              {(podDetails.sources_arxiv || podDetails.sources_ddg) && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium mb-2">Sources</h3>
                  <div className="space-y-4">
                    {/* Academic Papers */}
                    {podDetails.sources_arxiv && podDetails.sources_arxiv.length > 0 && (
                      <div>
                        <h4 className="text-base font-medium mb-2">Academic Papers</h4>
                        <div className="flex flex-col gap-2">
                          {podDetails.sources_arxiv.map((source, idx) => (
                            <SourceTag
                              key={`scholar-${idx}`}
                              source={source}
                              variant="lg"
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Web Sources */}
                    {podDetails.sources_ddg && podDetails.sources_ddg.length > 0 && (
                      <div>
                        <h4 className="text-base font-medium mb-2">Web Sources</h4>
                        <div className="flex flex-col gap-2">
                          {podDetails.sources_ddg.map((source, idx) => (
                            <SourceTag
                              key={`web-${idx}`}
                              source={source}
                              variant="lg"
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        {/* Similar Pods */}
        {podDetails && podDetails.similar_pods && podDetails.similar_pods.length > 0 && (
          <div>
            <h3 className="text-lg font-medium mb-4">Similar Research Pods</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {podDetails.similar_pods.map((pod) => (
                <PodCard key={pod.id} pod={pod} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
