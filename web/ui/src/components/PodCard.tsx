import type { FC } from 'react'
import { SourceTag } from '@/components/SourceTag'
import type { Pod } from '@/hooks/useWebAPI'

export const PodCard: FC<{
  pod: Pod
  onClick?: () => void
}> = ({ pod, onClick }) => {
  const statusColors = {
    QUEUED: 'badge-neutral',
    ASSIGNED: 'badge-info',
    PROCESSING: 'badge-warning',
    IN_PROGRESS: 'badge-warning',
    COMPLETED: 'badge-success',
    ERROR: 'badge-error',
  }

  return (
    <div
      className="card bg-base-100 shadow-xl cursor-pointer hover:shadow-2xl transition-shadow"
      onClick={onClick}
    >
      <div className="card-body py-4 px-5">
        <div className="card-title flex justify-between">
          <h2 className='truncate'>{pod.title}</h2>
          {pod.status && (
            <div className={`badge ${statusColors[pod.status]}`}>
              {pod.status}
            </div>
          )}
        </div>

        <div className="flex justify-between text-sm text-base-content/70">
          <span>
            {new Date(pod.created_at * 1000).toLocaleDateString()} • {new Date(pod.created_at * 1000).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
          </span>
        </div>

        {pod.audio_url && (
          <audio className="w-full mt-2" controls onClick={e => e.stopPropagation()}>
            <source src={pod.audio_url} type="audio/mpeg" />
            Your browser does not support the audio element.
          </audio>
        )}

        <div className="flex flex-wrap gap-2 mt-2">
          {pod.sources_ddg?.map((source, idx) => (
            <SourceTag
              key={`web-${idx}`}
              source={source}
            />
          ))}
          {pod.sources_arxiv?.map((source, idx) => (
            <SourceTag
              key={`scholar-${idx}`}
              source={source}
            />
          ))}
        </div>
      </div>
    </div>
  )
}