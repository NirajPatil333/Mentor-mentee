import { useEffect, useState, useRef } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import Avatar from '../components/Avatar'

function MenteeProfile() {
  const { user, updateUser } = useAuth()
  const fileInputRef = useRef(null)

  const [profile, setProfile] = useState({
    name: '',
    email: '',
    profile_picture: null,
    bio: '',
    education: '',
    learning_goal: '',
    experience_level: '',
  })

  // Profile picture state
  const [selectedFile, setSelectedFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [uploadingPic, setUploadingPic] = useState(false)
  const [picMessage, setPicMessage] = useState('')
  const [picError, setPicError] = useState('')

  // Shared catalog skills
  const [catalogSkills, setCatalogSkills] = useState([])

  // Section A: My Skills (Known skills)
  const [knownSkills, setKnownSkills] = useState([])
  const [knownSkillInput, setKnownSkillInput] = useState('')
  const [knownProficiency, setKnownProficiency] = useState('Intermediate')
  const [savingKnownSkills, setSavingKnownSkills] = useState(false)
  const [knownMessage, setKnownMessage] = useState('')
  const [knownError, setKnownError] = useState('')

  // Section B: Skills I Want to Learn (Learning Interests)
  const [interests, setInterests] = useState([])
  const [interestInput, setInterestInput] = useState('')
  const [interestPriority, setInterestPriority] = useState('High')
  const [savingInterests, setSavingInterests] = useState(false)
  const [interestMessage, setInterestMessage] = useState('')
  const [interestError, setInterestError] = useState('')

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
      const [profRes, skillsRes, interestsRes, catalogRes] = await Promise.all([
        api.get('/mentees/profile', { headers }),
        api.get('/mentees/skills', { headers }).catch(() => ({ data: { skills: [] } })),
        api.get('/mentees/interests', { headers }).catch(() => ({ data: { interests: [] } })),
        api.get('/skills').catch(() => ({ data: { skills: [] } })),
      ])

      const data = profRes.data.profile
      setProfile({
        name: data?.name || user?.name || '',
        email: data?.email || user?.email || '',
        profile_picture: data?.profile_picture || user?.profile_picture || null,
        bio: data?.bio || '',
        education: data?.education || '',
        learning_goal: data?.learning_goal || '',
        experience_level: data?.experience_level || '',
      })

      setKnownSkills(skillsRes.data.skills || [])
      setInterests(interestsRes.data.interests || [])
      setCatalogSkills(catalogRes.data.skills || [])
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load profile data.')
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

    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if (!allowedTypes.includes(file.type)) {
      setPicError('Please select a valid image file (JPG, PNG, WebP, or GIF).')
      return
    }

    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      setPicError('Image size exceeds 5MB limit. Please choose a smaller image.')
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

      const response = await api.post('/mentees/profile-picture', formData, {
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

      await api.delete('/mentees/profile-picture', { headers })

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
  // Section A: My Skills Handlers (Known Skills)
  // -------------------------------------------------------------------------
  const handleAddKnownSkill = async (e) => {
    e.preventDefault()
    setKnownMessage('')
    setKnownError('')

    const trimmed = knownSkillInput.trim()
    if (!trimmed) {
      setKnownError('Please select or type a skill you know.')
      return
    }

    const lower = trimmed.toLowerCase()
    if (knownSkills.some((s) => s.skill_name.toLowerCase() === lower)) {
      setKnownError(`'${trimmed}' is already in your known skills list.`)
      return
    }

    const matched = catalogSkills.find((s) => s.name.toLowerCase() === lower)
    const payload = matched
      ? { skill_id: matched.id, proficiency: knownProficiency }
      : { skill_name: trimmed, proficiency: knownProficiency }

    try {
      setSavingKnownSkills(true)
      const res = await api.post('/mentees/skills', payload, { headers })
      setKnownSkills(res.data.skills || [])
      setKnownSkillInput('')
      setKnownMessage(`Added '${trimmed}' to your skills.`)
    } catch (err) {
      setKnownError(err.response?.data?.message || 'Failed to add skill.')
    } finally {
      setSavingKnownSkills(false)
    }
  }

  const handleRemoveKnownSkill = async (skillId) => {
    try {
      setSavingKnownSkills(true)
      setKnownMessage('')
      setKnownError('')
      const res = await api.delete(`/mentees/skills/${skillId}`, { headers })
      setKnownSkills(res.data.skills || [])
      setKnownMessage('Skill removed.')
    } catch (err) {
      setKnownError(err.response?.data?.message || 'Failed to remove skill.')
    } finally {
      setSavingKnownSkills(false)
    }
  }

  // -------------------------------------------------------------------------
  // Section B: Skills I Want to Learn Handlers (Learning Interests)
  // -------------------------------------------------------------------------
  const handleAddInterest = async (e) => {
    e.preventDefault()
    setInterestMessage('')
    setInterestError('')

    const trimmed = interestInput.trim()
    if (!trimmed) {
      setInterestError('Please select or type a subject you want to learn.')
      return
    }

    const lower = trimmed.toLowerCase()
    if (interests.some((i) => i.skill_name.toLowerCase() === lower)) {
      setInterestError(`'${trimmed}' is already in your learning interests.`)
      return
    }

    const matched = catalogSkills.find((s) => s.name.toLowerCase() === lower)
    const payload = matched
      ? { skill_id: matched.id, priority: interestPriority }
      : { skill_name: trimmed, priority: interestPriority }

    try {
      setSavingInterests(true)
      const res = await api.post('/mentees/interests', payload, { headers })
      setInterests(res.data.interests || [])
      setInterestInput('')
      setInterestMessage(`Added '${trimmed}' to learning interests.`)
    } catch (err) {
      setInterestError(err.response?.data?.message || 'Failed to add interest.')
    } finally {
      setSavingInterests(false)
    }
  }

  const handleRemoveInterest = async (skillId) => {
    try {
      setSavingInterests(true)
      setInterestMessage('')
      setInterestError('')
      const res = await api.delete(`/mentees/interests/${skillId}`, { headers })
      setInterests(res.data.interests || [])
      setInterestMessage('Learning interest removed.')
    } catch (err) {
      setInterestError(err.response?.data?.message || 'Failed to remove interest.')
    } finally {
      setSavingInterests(false)
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

      await api.put('/mentees/profile', profile, { headers })

      setMessage('Profile updated successfully!')
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
          My Mentee Profile
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Manage your profile picture, known skills, learning interests, and educational goals.
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
          <div className="relative shrink-0">
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
                PNG, JPG, WebP or GIF up to 5MB. Displayed on mentorship requests, sessions, and dashboard.
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
      {/* 2. SECTION A: MY SKILLS (Technologies already known) */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-white rounded-xl p-6 md:p-8 shadow-xs border border-emerald-100 space-y-6 ring-1 ring-emerald-500/10">
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-emerald-100/70">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-xs border border-emerald-200/80">
              A
            </div>
            <div>
              <h2 className="text-base md:text-lg font-bold text-slate-900">
                My Skills
              </h2>
              <p className="text-xs text-slate-500">
                Technologies and tools you already know and can build with.
              </p>
            </div>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            Known Skills
          </span>
        </div>

        {knownMessage && (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200/80 p-3 text-sm text-emerald-700 font-medium">
            {knownMessage}
          </div>
        )}

        {knownError && (
          <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3 text-sm text-rose-700 font-medium">
            {knownError}
          </div>
        )}

        {/* Existing Known Skills Chips */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
            Existing Skills ({knownSkills.length})
          </label>

          {knownSkills.length === 0 ? (
            <div className="p-4 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-center text-xs text-slate-500">
              No existing skills added yet. Add technologies you currently know below.
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {knownSkills.map((s) => (
                <span
                  key={s.id || s.skill_id}
                  className="inline-flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-lg bg-emerald-50 text-emerald-900 border border-emerald-200 text-xs font-semibold shadow-2xs transition-all hover:bg-emerald-100/70"
                >
                  <span>{s.skill_name}</span>
                  {s.proficiency && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-200/70 text-emerald-800">
                      {s.proficiency}
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => handleRemoveKnownSkill(s.skill_id)}
                    disabled={savingKnownSkills}
                    className="w-4 h-4 rounded-full flex items-center justify-center text-emerald-700 hover:bg-emerald-300 hover:text-emerald-900 transition cursor-pointer"
                    title={`Remove ${s.skill_name}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Add Known Skill Form */}
        <form onSubmit={handleAddKnownSkill} className="pt-4 border-t border-slate-100">
          <label className="block text-xs font-semibold text-slate-700 mb-2">
            Add Known Skill
          </label>
          <div className="flex flex-col sm:flex-row gap-2.5">
            <div className="flex-1 relative">
              <input
                type="text"
                list="mentee-known-skills-datalist"
                value={knownSkillInput}
                onChange={(e) => setKnownSkillInput(e.target.value)}
                placeholder="Type or select a skill you know (e.g. JavaScript, HTML, Python)..."
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2 text-slate-900 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
              />
              <datalist id="mentee-known-skills-datalist">
                {catalogSkills.map((c) => (
                  <option key={c.id} value={c.name}>
                    {c.category}
                  </option>
                ))}
              </datalist>
            </div>

            <select
              value={knownProficiency}
              onChange={(e) => setKnownProficiency(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900 text-sm bg-white outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 cursor-pointer shrink-0"
            >
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
              <option value="Expert">Expert</option>
            </select>

            <button
              type="submit"
              disabled={savingKnownSkills || !knownSkillInput.trim()}
              className="bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-xs disabled:opacity-50 cursor-pointer shrink-0 flex items-center justify-center gap-1.5"
            >
              {savingKnownSkills ? 'Adding...' : '+ Add Known Skill'}
            </button>
          </div>
        </form>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 3. SECTION B: SKILLS I WANT TO LEARN (Learning Interests) */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-white rounded-xl p-6 md:p-8 shadow-xs border border-indigo-100 space-y-6 ring-1 ring-indigo-500/10">
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-indigo-100/70">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-xs border border-indigo-200/80">
              B
            </div>
            <div>
              <h2 className="text-base md:text-lg font-bold text-slate-900">
                Skills I Want to Learn
              </h2>
              <p className="text-xs text-slate-500">
                Technologies and subjects you want guidance from mentors on.
              </p>
            </div>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
            Learning Interests
          </span>
        </div>

        {interestMessage && (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200/80 p-3 text-sm text-emerald-700 font-medium">
            {interestMessage}
          </div>
        )}

        {interestError && (
          <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3 text-sm text-rose-700 font-medium">
            {interestError}
          </div>
        )}

        {/* Existing Learning Interests Chips */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
            Learning Targets ({interests.length})
          </label>

          {interests.length === 0 ? (
            <div className="p-4 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-center text-xs text-slate-500">
              No learning interests added yet. Add subjects you want to learn to get matched with mentors!
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {interests.map((item) => (
                <span
                  key={item.id || item.skill_id}
                  className="inline-flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-lg bg-indigo-50 text-indigo-900 border border-indigo-200 text-xs font-semibold shadow-2xs transition-all hover:bg-indigo-100/70"
                >
                  <span>{item.skill_name}</span>
                  {item.priority && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-indigo-200/70 text-indigo-800">
                      {item.priority} Priority
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => handleRemoveInterest(item.skill_id)}
                    disabled={savingInterests}
                    className="w-4 h-4 rounded-full flex items-center justify-center text-indigo-700 hover:bg-indigo-300 hover:text-indigo-900 transition cursor-pointer"
                    title={`Remove ${item.skill_name}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Add Learning Interest Form */}
        <form onSubmit={handleAddInterest} className="pt-4 border-t border-slate-100">
          <label className="block text-xs font-semibold text-slate-700 mb-2">
            Add Subject You Want to Learn
          </label>
          <div className="flex flex-col sm:flex-row gap-2.5">
            <div className="flex-1 relative">
              <input
                type="text"
                list="mentee-learning-skills-datalist"
                value={interestInput}
                onChange={(e) => setInterestInput(e.target.value)}
                placeholder="Type or select a subject to learn (e.g. Deep Learning, System Architecture)..."
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2 text-slate-900 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
              />
              <datalist id="mentee-learning-skills-datalist">
                {catalogSkills.map((c) => (
                  <option key={c.id} value={c.name}>
                    {c.category}
                  </option>
                ))}
              </datalist>
            </div>

            <select
              value={interestPriority}
              onChange={(e) => setInterestPriority(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900 text-sm bg-white outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 cursor-pointer shrink-0"
            >
              <option value="High">High Priority</option>
              <option value="Medium">Medium Priority</option>
              <option value="Low">Low Priority</option>
            </select>

            <button
              type="submit"
              disabled={savingInterests || !interestInput.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-xs disabled:opacity-50 cursor-pointer shrink-0 flex items-center justify-center gap-1.5"
            >
              {savingInterests ? 'Adding...' : '+ Add Target'}
            </button>
          </div>
        </form>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 4. GOALS & EDUCATIONAL BACKGROUND */}
      {/* ------------------------------------------------------------- */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 md:p-8 shadow-xs border border-slate-200/80 space-y-6"
      >
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h2 className="text-base md:text-lg font-bold text-slate-900">
            Education & Learning Goals
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
            rows="3"
            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm"
            placeholder="Tell mentors about yourself, your background, and your learning style..."
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
              placeholder="e.g. B.Tech Computer Science / Self-taught"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              Experience Level
            </label>
            <select
              name="experience_level"
              value={profile.experience_level}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm cursor-pointer"
            >
              <option value="">Select your experience level</option>
              <option value="Beginner">Beginner (0-1 years)</option>
              <option value="Intermediate">Intermediate (1-3 years)</option>
              <option value="Advanced">Advanced (3+ years)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">
            Learning / Career Goal
          </label>
          <textarea
            name="learning_goal"
            value={profile.learning_goal}
            onChange={handleChange}
            rows="3"
            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm"
            placeholder="e.g. Seeking mentorship to transition into a Full Stack role and contribute to open-source..."
          />
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

export default MenteeProfile
