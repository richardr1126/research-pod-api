import { type FC, useMemo } from 'react'

export const SourceTag: FC<{
  source: { title: string; url: string; authors: string | string[] } | { title: string; url: string; snippet?: string; keywords_used?: string[] }
  variant?: 'sm' | 'lg'
}> = ({ source, variant }) => {
  const type = useMemo(() => {
    if ('authors' in source) {
      return 'scholar';
    } else if ('keywords_used' in source) {
      return 'web';
    }
    return 'web';
  }, [source]);
  const emoji = useMemo(() => (type === 'web' ? '🌐' : '📚'), [type]);
  variant = variant ?? 'sm';

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`flex flex-col text-left items-start badge badge-${variant} badge-ghost tooltip tooltip-top hover:glass max-w-full ${variant === 'lg' ? 'h-fit p-2 px-4' : ''}`}
      data-tip={source.url}
      onClick={(e) => e.stopPropagation()}
    >
      <span className={`flex items-center max-w-full ${variant === 'lg' ? 'gap-2' : 'gap-1'}`}>
        <span className="flex-none">{emoji}</span>
        <span className={variant === 'sm' ? 'truncate' : ''}>{source.title}</span>
      </span>
      {variant === 'lg' && (
        <span className="text-xs text-base-content/70">
          {type === 'web' ? ('snippet' in source && source.snippet) || '' : ('authors' in source && source.authors) || ''}
        </span>
      )}
    </a>
  )
}