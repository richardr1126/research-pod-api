import type { FC } from 'react'
import { SourceTag } from './SourceTag'
import { Link } from '@tanstack/react-router'

export interface Pod {
  id: string
  query: string
  status?: 'QUEUED' | 'ASSIGNED' | 'PROCESSING' | 'IN_PROGRESS' | 'COMPLETED' | 'ERROR'
  progress?: number
  created_at: number
  updated_at?: number
  audio_url?: string
  transcript?: string
  sources_arxiv?: Array<{ title: string; url: string; authors: string | string[] }>
  sources_ddg?: Array<{ title: string; url: string; snippet?: string; keywords_used?: string[] }>
}

interface PodCardProps {
  pod: Pod
}

export const PodCard: FC<PodCardProps> = ({ pod }) => {
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
    >
      <div className="card-body py-4 px-5">
        <div className="card-title flex justify-between">
          <h2 className='truncate'>{pod.query}</h2>
          {pod.status && (
            <div className={`badge ${statusColors[pod.status]}`}>
              {pod.status}
            </div>
          )}
        </div>

        { pod.progress !== undefined && pod.progress < 100 && pod.status !== 'COMPLETED' ? (
          <progress
            className="progress progress-primary w-full"
            value={pod.progress}
            max="100"
          />
        ) : (
          <Link
            to={'/details/$podId'}
            params = {{ podId: pod.id }}
            className="btn btn-primary btn-sm mt-2"
            >
            View Details
          </Link>
        )}

        <div className="flex justify-between text-sm text-base-content/70">
          <span>
            {new Date(pod.created_at * 1000).toLocaleDateString()} • {new Date(pod.created_at * 1000).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
          </span>
        </div>

        {pod.audio_url && (
          <audio className="w-full mt-2" controls>
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