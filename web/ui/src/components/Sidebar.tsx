import { Link, useMatches } from '@tanstack/react-router'

export default function Sidebar() {
  const matches = useMatches()
  const currentPath = matches[matches.length - 1]?.pathname || '/'

  const isActive = (path: string): boolean => {
    if (path === '/' && (currentPath === '/' || currentPath.includes('/generating'))) return true
    return currentPath === path
  }

  const NavLinks = () => (
    <>
      <Link
        to="/"
        className={`btn btn-ghost justify-start ${isActive('/') ? 'btn-active' : ''}`}
      >
        Browse Podcasts
      </Link>
      <Link
        to="/create"
        className={`btn btn-ghost justify-start ${isActive('/create') ? 'btn-active' : ''}`}
      >
        Generate New Podcast
      </Link>
    </>
  )

  return (
    <>
      {/* Mobile Navbar */}
      <div className="md:hidden">
        <div className="navbar bg-base-100 shadow-lg fixed top-0 w-full z-50">
          <div className="navbar-start w-full">
            <div className="dropdown">
              <label tabIndex={0} className="btn btn-ghost">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </label>
              <ul tabIndex={0} className="menu dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
                <NavLinks />
              </ul>
            </div>
            <h2 className="text-xl font-bold ml-2 truncate">Research Pod</h2>
          </div>
        </div>
        <div className="h-16"></div> {/* Spacer for fixed navbar */}
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden md:block min-h-screen min-w-64 p-4 bg-base-100">
        <div className="mb-6">
          <h2 className="text-2xl font-bold mx-2">Research Pod</h2>
        </div>
        <div className="flex flex-col gap-2">
          <NavLinks />
        </div>
      </div>
    </>
  )
}
