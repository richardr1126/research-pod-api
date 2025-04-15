import type { FC } from 'react'
import type { ResearchPodDetails } from '@/hooks/useWebAPI'
import { SourceTag } from './SourceTag'
import { Link } from '@tanstack/react-router'
import { PodCard } from './PodCard'
import { useNavigate } from '@tanstack/react-router'

interface Props {
  pod: ResearchPodDetails
}

export const PodDetails: FC<Props> = ({ pod }) => {
    const navigate = useNavigate()

  return (
    <div className="bg-base-300 px-10">
    <div>
      <Link to="/" className="bg-base-700 text-primary hover:underline mb-4 px-5 py-7 btn btn-ghost justify-start">
    ← Back to all pods
  </Link>

    <div className="card bg-base-100 shadow-xl transition-shadow">
      
    <div className="p-4 bg-base card-body py-4 px-5">
      
      <h1 className="text-6xl font-bold mb-2 py-4 px-4">{pod.query}</h1>

      {pod.audio_url && (
        <audio className="w-full my-4 bg-base-300 px-10" controls>
          <source src={pod.audio_url} type="audio/mpeg" />
          Your browser does not support the audio element.
        </audio>
      )}

    {(pod.sources_ddg?.length || pod.sources_arxiv?.length) && (
        <>
          <h2 className="text-4xl font-semibold mt-6 mb-2 px-4">Sources</h2>
          <div className="flex flex-wrap gap-2">
            {pod.sources_ddg?.map((s, i) => (
              <SourceTag key={`ddg-${i}`} source={s} />
            ))}
            {pod.sources_arxiv?.map((s, i) => (
              <SourceTag key={`arxiv-${i}`} source={s} />
            ))}
          </div>
        </>
      )}
      

      {pod.transcript && (
        <>
          <h2 className="text-4xl font-semibold mt-6 mb-2 px-4">Transcript</h2>
          <p className="whitespace-pre-wrap text-base-content text-xl">{pod.transcript}</p>
        </>
      )}


    {pod && pod.similar_pods && pod.similar_pods.length > 0 && (
            <div className="mt-8">
            <h3 className="text-4xl font-semibold mb-4 px-4">Similar Research Pods</h3>
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
    <div className="text-sm text-base-content/70 mb-4 py-4 px-4">
        Created: {new Date(pod.created_at).toLocaleString()}
      </div>
    </div>
    </div>
  )
}