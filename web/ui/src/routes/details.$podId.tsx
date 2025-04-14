import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/details/$podId')({
  component: PodDetails,
})

function PodDetails() {
  const podId: String = Route.useParams().podId

  return <div>Podcast ID: {podId}</div>
}
