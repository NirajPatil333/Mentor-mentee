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
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading profile...</span>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          My Mentor Profile
        </h1>

        <p className="text-slate-500 text-sm mt-1">
          Update your professional bio, experience, and availability for mentees.
        </p>
      </div>

      {message && (
        <div className="rounded-lg bg-emerald-50 border border-emerald-200/80 p-3.5 text-sm text-emerald-700 font-medium">
          {message}
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3.5 text-sm text-rose-700 font-medium">
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 md:p-8 shadow-xs border border-slate-200/80 space-y-6"
      >
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">
            Bio
          </label>

          <textarea
            name="bio"
            value={profile.bio}
            onChange={handleChange}
            rows="4"
            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm"
            placeholder="Tell mentees about your expertise and background..."
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              Education
            </label>

            <input
              type="text"
              name="education"
              value={profile.education}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm"
              placeholder="e.g. B.E. Computer Engineering"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              Current Position
            </label>

            <input
              type="text"
              name="current_position"
              value={profile.current_position}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm"
              placeholder="e.g. Senior Software Engineer"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              Experience (Years)
            </label>

            <input
              type="number"
              name="experience_years"
              min="0"
              value={profile.experience_years}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              Availability Status
            </label>

            <select
              name="availability_status"
              value={profile.availability_status}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm cursor-pointer"
            >
              <option value="available">Available</option>
              <option value="busy">Busy</option>
              <option value="unavailable">Unavailable</option>
            </select>
          </div>
        </div>

        <div className="pt-2 border-t border-slate-100">
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer text-sm"
          >
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default MentorProfileEdit