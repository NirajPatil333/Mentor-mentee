import { Outlet } from 'react-router-dom'

function DashboardLayout() {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white border-b p-4">
        <h1 className="text-xl font-bold">
          Mentor-Mentee Platform
        </h1>
      </header>

      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}

export default DashboardLayout