import { useLocation, useNavigate } from 'react-router-dom'

function MentorProfile() {
  const location = useLocation()
  const navigate = useNavigate()

  const mentor = location.state?.mentor

  if (!mentor) {
    return (
      <div>
        <h1 className="text-2xl font-bold">
          Mentor not found
        </h1>

        <button
          onClick={() => navigate('/dashboard/mentee')}
          className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => navigate('/dashboard/mentee')}
        className="mb-6 text-blue-600 hover:underline"
      >
        ← Back to Dashboard
      </button>

      <div className="bg-white rounded-xl p-8 shadow-sm">

        <h1 className="text-3xl font-bold">
          {mentor.name}
        </h1>

        <p className="text-gray-500 mt-1">
          {mentor.current_position || 'Mentor'}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">

          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-500">
              Experience
            </p>

            <p className="text-xl font-semibold mt-1">
              {mentor.experience_years} years
            </p>
          </div>

          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-500">
              Rating
            </p>

            <p className="text-xl font-semibold mt-1">
              {mentor.average_rating} / 5
            </p>
          </div>

          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-500">
              Availability
            </p>

            <p className="text-xl font-semibold mt-1 capitalize">
              {mentor.availability_status}
            </p>
          </div>

        </div>

        <div className="mt-8">
          <h2 className="text-xl font-bold">
            About
          </h2>

          <p className="text-gray-600 mt-2">
            {mentor.bio || 'No bio available yet.'}
          </p>
        </div>

        <div className="mt-8">
          <h2 className="text-xl font-bold">
            Education
          </h2>

          <p className="text-gray-600 mt-2">
            {mentor.education || 'No education information available yet.'}
          </p>
        </div>

        <button
          className="mt-8 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
        >
          Send Mentorship Request
        </button>

      </div>
    </div>
  )
}

export default MentorProfile