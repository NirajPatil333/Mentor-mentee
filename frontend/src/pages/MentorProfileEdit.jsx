import { useEffect, useState } from 'react'
import api from '../services/api'

function MentorProfileEdit() {
  const [profile, setProfile] = useState({
    bio: '',
    education: '',
    experience_years: 0,
    current_position: '',
    availability_status: 'available',
  })

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const token = localStorage.getItem('token')

  const fetchProfile = async () => {
    try {
      const response = await api.get('/mentors/profile', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      const data = response.data.profile

      setProfile({
        bio: data?.bio || '',
        education: data?.education || '',
        experience_years: data?.experience_years || 0,
        current_position: data?.current_position || '',
        availability_status:
          data?.availability_status || 'available',
      })
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Failed to load profile.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  const handleChange = (e) => {
    setProfile({
      ...profile,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      setSaving(true)
      setMessage('')
      setError('')

      await api.put('/mentors/profile', {
        ...profile,
        experience_years: Number(profile.experience_years),
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setMessage('Profile updated successfully!')
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Failed to update profile.'
      )
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <p>Loading profile...</p>
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">
        My Profile
      </h1>

      <p className="text-gray-500 mt-1">
        Update your mentor profile.
      </p>

      {message && (
        <p className="mt-4 text-green-600">
          {message}
        </p>
      )}

      {error && (
        <p className="mt-4 text-red-600">
          {error}
        </p>
      )}

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg p-6 mt-6 shadow-sm space-y-5"
      >
        <div>
          <label className="block text-sm font-medium mb-1">
            Bio
          </label>

          <textarea
            name="bio"
            value={profile.bio}
            onChange={handleChange}
            rows="4"
            className="w-full border rounded-lg px-3 py-2"
            placeholder="Tell mentees about yourself..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Education
          </label>

          <input
            type="text"
            name="education"
            value={profile.education}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="e.g. B.E. Computer Engineering"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Current Position
          </label>

          <input
            type="text"
            name="current_position"
            value={profile.current_position}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="e.g. Software Developer"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Experience (Years)
          </label>

          <input
            type="number"
            name="experience_years"
            min="0"
            value={profile.experience_years}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Availability
          </label>

          <select
            name="availability_status"
            value={profile.availability_status}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
          >
            <option value="available">Available</option>
            <option value="busy">Busy</option>
            <option value="unavailable">Unavailable</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </form>
    </div>
  )
}

export default MentorProfileEdit