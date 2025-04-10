import Sidebar from '@/components/Sidebar'
import { Outlet, createRootRoute } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'

export const Route = createRootRoute({
  component: () => (
    <>
      <div className="flex flex-col md:flex-row min-h-screen mx-auto">
        <Sidebar />
        <div className="w-full">
          <Outlet />
        </div>
      </div>
      <TanStackRouterDevtools />
    </>
  ),
})
