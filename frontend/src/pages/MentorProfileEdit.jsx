import { useEffect, useState, useRef } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import Avatar from '../components/Avatar'

function MentorProfileEdit() {
  const { user, updateUser } = useAuth()
  const fileInputRef = useRef(null)

  const [profile, setProfile] = useState({
    name: '',
    email: '',
    profile_picture: null,
    bio: '',
    education: '',
    experience_years: 0,
    current_position: '',
    availability_status: 'available',
  })

  // Profile picture state
  const [selectedFile, setSelectedFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [uploadingPic, setUploadingPic] = useState(false)
  const [picMessage, setPicMessage] = useState('')
  const [picError, setPicError] = useState('')

  // Skills state
  const [skills, setSkills] = useState([])
  const [catalogSkills, setCatalogSkills] = useState([])
  const [selectedSkillInput, setSelectedSkillInput] = useState('')
  const [selectedProficiency, setSelectedProficiency] = useState('Intermediate')
  const [savingSkills, setSavingSkills] = useState(false)
  const [skillsMessage, setSkillsMessage] = useState('')
  const [skillsError, setSkillsError] = useState('')

  // General profile state
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const token = localStorage.getItem('token')
  const headers = { Authorization: `Bearer ${token}` }

  const fetchData = async () => {
    try {
      setLoading(true)
      const [profRes, skillsRes, catalogRes] = await Promise.all([
        api.get('/mentors/profile', { headers }),
        api.get('/mentors/skills', { headers }).catch(() => ({ data: { skills: [] } })),
        api.get('/skills').catch(() => ({ data: { skills: [] } })),
      ])

      const data = profRes.data.profile
      setProfile({
        name: data?.name || user?.name || '',
        email: data?.email || user?.email || '',
        profile_picture: data?.profile_picture || user?.profile_picture || null,
        bio: data?.bio || '',
        education: data?.education || '',
        experience_years: data?.experience_years || 0,
        current_position: data?.current_position || '',
        availability_status: data?.availability_status || 'available',
      })

      setSkills(skillsRes.data.skills || [])
      setCatalogSkills(catalogRes.data.skills || [])
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load mentor profile.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // -------------------------------------------------------------------------
  // Profile Picture Handlers
  // -------------------------------------------------------------------------
  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    setPicMessage('')
    setPicError('')

    if (!file) return

    // Client-side file validation
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if (!allowedTypes.includes(file.type)) {
      setPicError('Please select a valid image file (JPG, PNG, WebP, or GIF).')
      return
    }

    const maxSize = 5 * 1024 * 1024 // 5MB
    if (file.size > maxSize) {
      setPicError('Image size exceeds 5MB. Please choose a smaller image.')
      return
    }

    setSelectedFile(file)
    const previewUrl = URL.createObjectURL(file)
    setImagePreview(previewUrl)
  }

  const handleCancelPreview = () => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview)
    }
    setImagePreview(null)
    setSelectedFile(null)
    setPicError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleUploadPicture = async () => {
    if (!selectedFile) return

    try {
      setUploadingPic(true)
      setPicMessage('')
      setPicError('')

      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await api.post('/mentors/profile-picture', formData, {
        headers: {
          ...headers,
          'Content-Type': 'multipart/form-data',
        },
      })

      const newPicPath = response.data.profile_picture
      setProfile((prev) => ({ ...prev, profile_picture: newPicPath }))
      updateUser({ profile_picture: newPicPath })

      handleCancelPreview()
      setPicMessage('Profile picture updated successfully!')
    } catch (err) {
      setPicError(err.response?.data?.message || 'Failed to upload profile picture.')
    } finally {
      setUploadingPic(false)
    }
  }

  const handleRemovePicture = async () => {
    try {
      setUploadingPic(true)
      setPicMessage('')
      setPicError('')

      await api.delete('/mentors/profile-picture', { headers })

      setProfile((prev) => ({ ...prev, profile_picture: null }))
      updateUser({ profile_picture: null })
      handleCancelPreview()
      setPicMessage('Profile picture removed.')
    } catch (err) {
      setPicError(err.response?.data?.message || 'Failed to remove profile picture.')
    } finally {
      setUploadingPic(false)
    }
  }

  // -------------------------------------------------------------------------
  // Skills Management Handlers
  // -------------------------------------------------------------------------
  const handleAddSkill = async (e) => {
    e.preventDefault()
    setSkillsMessage('')
    setSkillsError('')

    const trimmed = selectedSkillInput.trim()
    if (!trimmed) {
      setSkillsError('Please select or type a skill name.')
      return
    }

    // Check duplicate in local list
    const lower = trimmed.toLowerCase()
    if (skills.some((s) => s.skill_name.toLowerCase() === lower)) {
      setSkillsError(`You already have '${trimmed}' in your skills list.`)
      return
    }

    // Check if matched in catalog
    const matched = catalogSkills.find((s) => s.name.toLowerCase() === lower)
    const payload = matched
      ? { skill_id: matched.id, proficiency: selectedProficiency }
      : { skill_name: trimmed, proficiency: selectedProficiency }

    try {
      setSavingSkills(true)
      const res = await api.post('/mentors/skills', payload, { headers })
      setSkills(res.data.skills || [])
      setSelectedSkillInput('')
      setSkillsMessage(`Added skill '${trimmed}' (${selectedProficiency})`)
    } catch (err) {
      setSkillsError(err.response?.data?.message || 'Failed to add skill.')
    } finally {
      setSavingSkills(false)
    }
  }

  const handleRemoveSkill = async (skillId) => {
    try {
      setSavingSkills(true)
      setSkillsMessage('')
      setSkillsError('')
      const res = await api.delete(`/mentors/skills/${skillId}`, { headers })
      setSkills(res.data.skills || [])
      setSkillsMessage('Skill removed successfully.')
    } catch (err) {
      setSkillsError(err.response?.data?.message || 'Failed to remove skill.')
    } finally {
      setSavingSkills(false)
    }
  }

  // -------------------------------------------------------------------------
  // General Profile Handlers
  // -------------------------------------------------------------------------
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
      }, { headers })

      setMessage('Profile details updated successfully!')
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update profile.')
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
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          My Mentor Profile
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Manage your profile picture, professional background, expertise, and availability.
        </p>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 1. PROFILE PICTURE CARD */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-white rounded-xl p-6 md:p-8 shadow-xs border border-slate-200/80">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h2 className="text-base md:text-lg font-bold text-slate-900">
            Profile Picture
          </h2>
        </div>

        {picMessage && (
          <div className="mb-4 rounded-lg bg-emerald-50 border border-emerald-200/80 p-3 text-sm text-emerald-700 font-medium">
            {picMessage}
          </div>
        )}

        {picError && (
          <div className="mb-4 rounded-lg bg-rose-50 border border-rose-200/80 p-3 text-sm text-rose-700 font-medium">
            {picError}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center gap-6">
          <div className="relative group shrink-0">
            {imagePreview ? (
              <div className="relative">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-24 h-24 rounded-full object-cover border-2 border-blue-500 shadow-md ring-4 ring-blue-50"
                />
                <span className="absolute -top-1 -right-1 bg-blue-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full shadow-xs">
                  Preview
                </span>
              </div>
            ) : (
              <Avatar
                src={profile.profile_picture}
                name={profile.name || user?.name}
                size="2xl"
                className="ring-4 ring-slate-100"
              />
            )}
          </div>

          <div className="flex-1 space-y-3 text-center sm:text-left">
            <div>
              <p className="text-sm font-semibold text-slate-800">
                {imagePreview ? 'Image preview ready' : profile.profile_picture ? 'Custom profile photo' : 'Default avatar'}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                PNG, JPG, WebP or GIF up to 5MB. Displayed across your dashboard, mentor cards and requests.
              </p>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/png, image/jpeg, image/webp, image/gif"
              className="hidden"
            />

            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5 pt-1">
              {imagePreview ? (
                <>
                  <button
                    type="button"
                    onClick={handleUploadPicture}
                    disabled={uploadingPic}
                    className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-xs cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {uploadingPic ? (
                      <>
                        <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Saving...</span>
                      </>
                    ) : (
                      <span>Save Picture</span>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelPreview}
                    disabled={uploadingPic}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3.5 py-2 rounded-lg transition cursor-pointer"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1.5"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    <span>Choose Picture</span>
                  </button>

                  {profile.profile_picture && (
                    <button
                      type="button"
                      onClick={handleRemovePicture}
                      disabled={uploadingPic}
                      className="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold px-3.5 py-2 rounded-lg transition cursor-pointer disabled:opacity-50"
                    >
                      {uploadingPic ? 'Removing...' : 'Remove Picture'}
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 2. SKILLS & TECHNICAL EXPERTISE */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-white rounded-xl p-6 md:p-8 shadow-xs border border-slate-200/80 space-y-6">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          <div>
            <h2 className="text-base md:text-lg font-bold text-slate-900">
              Skills & Technical Expertise
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Highlight technologies and skills you can teach or guide mentees in.
            </p>
          </div>
        </div>

        {skillsMessage && (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200/80 p-3 text-sm text-emerald-700 font-medium">
            {skillsMessage}
          </div>
        )}

        {skillsError && (
          <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3 text-sm text-rose-700 font-medium">
            {skillsError}
          </div>
        )}

        {/* Existing Skills Chips */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
            Current Skills ({skills.length})
          </label>

          {skills.length === 0 ? (
            <div className="p-4 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-center text-xs text-slate-500">
              No skills added yet. Select or enter your technical skills below.
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {skills.map((s) => (
                <span
                  key={s.id || s.skill_id}
                  className="inline-flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-lg bg-blue-50 text-blue-900 border border-blue-200 text-xs font-semibold shadow-2xs transition-all hover:bg-blue-100/70"
                >
                  <span>{s.skill_name}</span>
                  {s.proficiency && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-blue-200/70 text-blue-800">
                      {s.proficiency}
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(s.skill_id)}
                    disabled={savingSkills}
                    className="w-4 h-4 rounded-full flex items-center justify-center text-blue-700 hover:bg-blue-300 hover:text-blue-900 transition cursor-pointer"
                    title={`Remove ${s.skill_name}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Add Skill Form */}
        <form onSubmit={handleAddSkill} className="pt-4 border-t border-slate-100">
          <label className="block text-xs font-semibold text-slate-700 mb-2">
            Add New Skill
          </label>
          <div className="flex flex-col sm:flex-row gap-2.5">
            <div className="flex-1 relative">
              <input
                type="text"
                list="mentor-skills-datalist"
                value={selectedSkillInput}
                onChange={(e) => setSelectedSkillInput(e.target.value)}
                placeholder="Type or select a skill (e.g., Python, React, AWS)..."
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2 text-slate-900 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />
              <datalist id="mentor-skills-datalist">
                {catalogSkills.map((c) => (
                  <option key={c.id} value={c.name}>
                    {c.category}
                  </option>
                ))}
              </datalist>
            </div>

            <select
              value={selectedProficiency}
              onChange={(e) => setSelectedProficiency(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900 text-sm bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 cursor-pointer shrink-0"
            >
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
              <option value="Expert">Expert</option>
            </select>

            <button
              type="submit"
              disabled={savingSkills || !selectedSkillInput.trim()}
              className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-xs disabled:opacity-50 cursor-pointer shrink-0 flex items-center justify-center gap-1.5"
            >
              {savingSkills ? 'Adding...' : '+ Add Skill'}
            </button>
          </div>
        </form>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 3. PROFESSIONAL PROFILE DETAILS */}
      {/* ------------------------------------------------------------- */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 md:p-8 shadow-xs border border-slate-200/80 space-y-6"
      >
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <h2 className="text-base md:text-lg font-bold text-slate-900">
            Professional Information
          </h2>
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
            placeholder="Tell mentees about your expertise, experience, and mentoring style..."
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
              placeholder="e.g. B.E. Computer Engineering / M.S. AI"
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
              placeholder="e.g. Senior Software Engineer at Tech Corp"
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

        <div className="pt-2 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer text-sm"
          >
            {saving ? 'Saving...' : 'Save Profile Changes'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default MentorProfileEdit
