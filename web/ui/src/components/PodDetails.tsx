import type { FC } from 'react'
import type { Pod } from '@/hooks/useWebAPI'
import { SourceTag } from './SourceTag'
import { Link } from '@tanstack/react-router'
import { PodCard } from './PodCard'
import { useNavigate } from '@tanstack/react-router'

export const PodDetails: FC<{
  pod: Pod
}> = ({ pod }) => {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-base-300 mx-auto px-4 md:p-8">
      <div>
        <Link to="/" className="bg-base-700 text-primary hover:underline btn btn-ghost my-2">
          ← Back to all pods
        </Link>

        <div className="card bg-base-100 shadow-xl transition-shadow">

          <div className="p-4 md:p-6 bg-base card-body">

            <h1 className="text-3xl md:text-5xl font-bold w-fit">{pod.title}</h1>
            <h2 className="font-bold">Research query: {pod.query}</h2>

            <div className="text-sm text-base-content/70">
              Created: {new Date(pod.created_at * 1000).toLocaleString()}
            </div>

            {/* Audio player */}
            {pod.audio_url && (
              <audio className="w-full my-4 flex" controls>
                <source src={pod.audio_url} type="audio/mpeg" />
                Your browser does not support the audio element.
              </audio>
            )}

            {/* Sources */}
            {(pod.sources_ddg?.length || pod.sources_arxiv?.length) && (
              <>
                <h2 className="text-2xl md:text-4xl font-semibold">Sources</h2>
                <div className="flex flex-wrap gap-2 mb-4">
                  {pod.sources_ddg?.map((s, i) => (
                    <SourceTag variant='lg' key={`ddg-${i}`} source={s} />
                  ))}
                  {pod.sources_arxiv?.map((s, i) => (
                    <SourceTag variant='lg' key={`arxiv-${i}`} source={s} />
                  ))}
                </div>
              </>
            )}

            {/* Transcript */}
            {pod.transcript && (
              <>
                <h2 className="text-2xl md:text-4xl font-semibold">Transcript</h2>
                <p className="whitespace-pre-wrap mb-4">{pod.transcript}</p>
              </>
            )}


          </div>

        </div>
        {/* Similar Pods */}
        {pod && pod.similar_pods && pod.similar_pods.length > 0 && (
          <div className="mt-4">
            <h3 className="text-2xl md:text-4xl font-semibold mb-4">Similar Research Pods</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pod.similar_pods.map((similarPod) => (
                <PodCard
                  key={similarPod.id}
                  pod={similarPod}
                  onClick={() => {
                    navigate({ to: `/pod/${similarPod.id}` })
                  }}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}