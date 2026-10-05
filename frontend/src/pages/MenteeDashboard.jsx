import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

function MenteeDashboard() {
  const [mentors, setMentors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const token = localStorage.getItem('token')

        const response = await api.get('/mentors/recommendations', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        console.log(
          'RECOMMENDATIONS:',
          JSON.stringify(response.data.recommendations, null, 2)
        )

        setMentors(response.data.recommendations || [])
      } catch (err) {
        console.error('Failed to load mentor recommendations:', err)

        setError(
          err.response?.data?.message ||
          'Unable to load mentor recommendations'
        )
      } finally {
        setLoading(false)
      }
    }

    fetchRecommendations()
  }, [])

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Mentee Dashboard
        </h1>

        <p className="mt-2 text-gray-600">
          Find the right mentors and manage your learning journey.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <p className="text-sm text-gray-500">
            Recommended Mentors
          </p>

          <p className="text-3xl font-bold mt-2">
            {mentors.length}
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <p className="text-sm text-gray-500">
            Mentorship Requests
          </p>

          <p className="text-3xl font-bold mt-2">
            0
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <p className="text-sm text-gray-500">
            Upcoming Sessions
          </p>

          <p className="text-3xl font-bold mt-2">
            0
          </p>
        </div>

      </div>

      {/* Recommended Mentors */}
      <div className="bg-white rounded-xl p-6 shadow-sm">

        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900">
            Recommended Mentors
          </h2>

          <p className="text-sm text-gray-500 mt-1">
            Mentors matched with your learning interests.
          </p>
        </div>

        {loading && (
          <p className="text-gray-500">
            Loading mentors...
          </p>
        )}

        {error && (
          <p className="text-red-500">
            {error}
          </p>
        )}

        {!loading && !error && mentors.length === 0 && (
          <div className="py-8 text-center">
            <p className="text-gray-500">
              No mentor recommendations available yet.
            </p>

            <p className="text-sm text-gray-400 mt-2">
              Add your learning interests to get matched with mentors.
            </p>
          </div>
        )}

        {!loading && !error && mentors.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">

            {mentors.map((recommendation) => {
              const mentor = recommendation.mentor

              return (
                <div
                  key={mentor.id}
                  className="border rounded-lg p-5 hover:shadow-md transition"
                >

                  <h3 className="font-bold text-lg">
                    {mentor.name}
                  </h3>

                  <p className="text-sm text-gray-500 mt-1">
                    {mentor.current_position || 'Mentor'}
                  </p>

                  <div className="mt-4 space-y-2 text-sm">

                    <p>
                      <span className="font-medium">
                        Experience:
                      </span>{' '}
                      {mentor.experience_years} years
                    </p>

                    <p>
                      <span className="font-medium">
                        Rating:
                      </span>{' '}
                      {mentor.average_rating} / 5
                    </p>

                    <p>
                      <span className="font-medium">
                        Match:
                      </span>{' '}
                      {recommendation.match_score}%
                    </p>

                  </div>

                  <button
                    onClick={() =>
                      navigate('/dashboard/mentor-profile', {
                        state: {
                          mentor: mentor,
                        },
                      })
                    }
                    className="mt-5 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                  >
                    View Profile
                  </button>
                </div>
              )
            })}

          </div>
        )}

      </div>
    </div>
  )
}

export default MenteeDashboard