import { useEffect, useState } from 'react'
import api from '../services/api'

function MenteeProfile() {
  const [profile, setProfile] = useState({
    bio: '',
    education: '',
    learning_goal: '',
    experience_level: '',
  })

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const token = localStorage.getItem('token')

  const fetchProfile = async () => {
    try {
      const response = await api.get('/mentees/profile', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setProfile({
        bio: response.data.profile?.bio || '',
        education: response.data.profile?.education || '',
        learning_goal:
          response.data.profile?.learning_goal || '',
        experience_level:
          response.data.profile?.experience_level || '',
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

      await api.put('/mentees/profile', profile, {
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
        Update your learning profile.
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
            placeholder="Tell mentors about yourself..."
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
            Learning Goal
          </label>

          <textarea
            name="learning_goal"
            value={profile.learning_goal}
            onChange={handleChange}
            rows="3"
            className="w-full border rounded-lg px-3 py-2"
            placeholder="What do you want to learn?"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Experience Level
          </label>

          <select
            name="experience_level"
            value={profile.experience_level}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
          >
            <option value="">Select level</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
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

export default MenteeProfile