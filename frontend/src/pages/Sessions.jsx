import { useEffect, useState } from 'react'
import api from '../services/api'
import { getSessionTimingState } from '../utils/sessionTiming'

function Sessions() {
    const [requests, setRequests] = useState([])
    const [sessions, setSessions] = useState([])

    const [title, setTitle] = useState('')
    const [description, setDescription] = useState('')
    const [requestId, setRequestId] = useState('')
    const [scheduledDate, setScheduledDate] = useState('')
    const [startTime, setStartTime] = useState('')
    const [endTime, setEndTime] = useState('')

    const [loading, setLoading] = useState(true)
    const [message, setMessage] = useState('')
    const [error, setError] = useState('')

    // Add-mentee panel state per session
    const [addMenteePanelId, setAddMenteePanelId] = useState(null)
    const [availableMentees, setAvailableMentees] = useState([])
    const [loadingMentees, setLoadingMentees] = useState(false)
    const [addingMenteeId, setAddingMenteeId] = useState(null)
    const [panelError, setPanelError] = useState('')

    const token = localStorage.getItem('token')

    const fetchData = async () => {
        try {
            const headers = { Authorization: `Bearer ${token}` }

            const requestsResponse = await api.get('/requests/received', { headers })
            const sessionsResponse = await api.get('/sessions', { headers })

            const acceptedRequests = (requestsResponse.data.requests || []).filter(
                (r) => r.status === 'accepted'
            )

            setRequests(acceptedRequests)
            setSessions(sessionsResponse.data.sessions || [])
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to load sessions.')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [])

    const handleCreateSession = async (e) => {
        e.preventDefault()
        try {
            setMessage('')
            setError('')

            await api.post(
                '/sessions',
                {
                    request_id: Number(requestId),
                    title,
                    description,
                    scheduled_date: scheduledDate,
                    start_time: startTime,
                    end_time: endTime,
                },
                { headers: { Authorization: `Bearer ${token}` } }
            )

            setMessage('Session created successfully!')
            setTitle('')
            setDescription('')
            setRequestId('')
            setScheduledDate('')
            setStartTime('')
            setEndTime('')

            fetchData()
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to create session.')
        }
    }

    const openAddMenteePanel = async (sessionId) => {
        if (addMenteePanelId === sessionId) {
            setAddMenteePanelId(null)
            return
        }
        setAddMenteePanelId(sessionId)
        setPanelError('')
        setAvailableMentees([])
        setLoadingMentees(true)
        try {
            const res = await api.get(`/sessions/${sessionId}/available-mentees`, {
                headers: { Authorization: `Bearer ${token}` },
            })
            setAvailableMentees(res.data.mentees || [])
        } catch (err) {
            setPanelError(err.response?.data?.message || 'Failed to load available mentees.')
        } finally {
            setLoadingMentees(false)
        }
    }

    const handleAddMentee = async (sessionId, menteeId) => {
        setAddingMenteeId(menteeId)
        setPanelError('')
        try {
            await api.post(
                `/sessions/${sessionId}/participants`,
                { mentee_id: menteeId },
                { headers: { Authorization: `Bearer ${token}` } }
            )
            // Refresh sessions and reset panel
            await fetchData()
            setAddMenteePanelId(null)
            setMessage('Mentee added to session successfully!')
        } catch (err) {
            setPanelError(err.response?.data?.message || 'Failed to add mentee.')
        } finally {
            setAddingMenteeId(null)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
                <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="font-medium text-sm">Loading sessions...</span>
            </div>
        )
    }

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
                    Sessions
                </h1>
                <p className="text-slate-500 text-sm mt-1">
                    Schedule and manage mentorship sessions with your mentees.
                </p>
            </div>

            {message && (
                <div className="rounded-lg bg-emerald-50 border border-emerald-200/80 p-3.5 text-sm text-emerald-700 font-medium flex justify-between items-center">
                    <span>{message}</span>
                    <button onClick={() => setMessage('')} className="font-bold ml-4 hover:opacity-75 cursor-pointer">×</button>
                </div>
            )}

            {error && (
                <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3.5 text-sm text-rose-700 font-medium flex justify-between items-center">
                    <span>{error}</span>
                    <button onClick={() => setError('')} className="font-bold ml-4 hover:opacity-75 cursor-pointer">×</button>
                </div>
            )}

            {/* Schedule Session Form */}
            <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-5">
                <div className="border-b border-slate-100 pb-3">
                    <h2 className="text-lg font-bold text-slate-900">Schedule New Session</h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                        Select an accepted mentee and specify time slot details.
                    </p>
                </div>

                <form onSubmit={handleCreateSession} className="space-y-4">
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">
                            Mentee
                        </label>
                        <select
                            value={requestId}
                            onChange={(e) => setRequestId(e.target.value)}
                            required
                            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
                        >
                            <option value="">Select mentee</option>
                            {requests.map((r) => (
                                <option key={r.id} value={r.id}>
                                    {r.mentee?.name || 'Mentee'}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">
                            Session Title
                        </label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="e.g. React Learning Session"
                            required
                            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">
                            Description
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="What topics or goals will be discussed?"
                            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
                            rows="3"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1">Date</label>
                            <input
                                type="date"
                                value={scheduledDate}
                                onChange={(e) => setScheduledDate(e.target.value)}
                                required
                                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1">Start Time</label>
                            <input
                                type="time"
                                value={startTime}
                                onChange={(e) => setStartTime(e.target.value)}
                                required
                                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1">End Time</label>
                            <input
                                type="time"
                                value={endTime}
                                onChange={(e) => setEndTime(e.target.value)}
                                required
                                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
                            />
                        </div>
                    </div>

                    <div className="pt-2">
                        <button
                            type="submit"
                            className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold px-5 py-2.5 rounded-lg transition-all duration-200 shadow-xs text-sm cursor-pointer"
                        >
                            Schedule Session
                        </button>
                    </div>
                </form>
            </div>

            {/* Existing Sessions */}
            <div className="space-y-4">
                <h2 className="text-lg font-bold text-slate-900">My Scheduled Sessions</h2>

                <div className="space-y-4">
                    {sessions.length === 0 ? (
                        <div className="bg-white rounded-xl p-8 border border-slate-200/80 shadow-xs text-center py-12">
                            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <h3 className="text-base font-semibold text-slate-800">No sessions scheduled yet</h3>
                            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                                Schedule a session using the form above to meet with your mentees.
                            </p>
                        </div>
                    ) : (
                        sessions.map((session) => {
                            const timing = getSessionTimingState(session)
                            const isAddPanelOpen = addMenteePanelId === session.id

                            return (
                                <div
                                    key={session.id}
                                    className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 hover:border-slate-300 hover:shadow-md transition-all duration-200 flex flex-col gap-4"
                                >
                                    <div className="space-y-3">
                                        <div className="flex justify-between items-start gap-3">
                                            <div>
                                                <h3 className="text-lg font-bold text-slate-900">{session.title}</h3>
                                                {session.description && (
                                                    <p className="text-sm text-slate-600 mt-1">{session.description}</p>
                                                )}
                                            </div>
                                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize shrink-0 ${timing.badgeClass}`}>
                                                {timing.displayStatus}
                                            </span>
                                        </div>

                                        <div className="flex flex-wrap gap-4 text-xs font-medium text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
                                            <span className="flex items-center gap-1.5">
                                                <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                </svg>
                                                <span>Date:</span> <strong className="text-slate-900">{session.scheduled_date}</strong>
                                            </span>
                                            <span className="flex items-center gap-1.5">
                                                <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                                <span>Time:</span> <strong className="text-slate-900">{session.start_time} – {session.end_time}</strong>
                                            </span>
                                            {session.domain && (
                                                <span className="flex items-center gap-1.5">
                                                    <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
                                                    </svg>
                                                    <span>Domain:</span> <strong className="text-slate-900">@{session.domain}</strong>
                                                </span>
                                            )}
                                        </div>

                                        {/* Participants list */}
                                        {session.participants && session.participants.length > 0 && (
                                            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                                                <p className="text-xs font-semibold text-blue-700 mb-2 flex items-center gap-1.5">
                                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                                                    </svg>
                                                    Participants ({session.participants.length})
                                                </p>
                                                <div className="flex flex-wrap gap-2">
                                                    {session.participants.map((p) => (
                                                        <span
                                                            key={p.id}
                                                            className="inline-flex items-center gap-1 bg-white border border-blue-200 text-blue-800 text-xs font-medium px-2.5 py-1 rounded-full"
                                                        >
                                                            <span className="w-4 h-4 rounded-full bg-blue-200 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0">
                                                                {(p.name || p.email || '?')[0].toUpperCase()}
                                                            </span>
                                                            {p.name || p.email}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Action row */}
                                    <div className="flex flex-wrap items-center gap-3 pt-1">
                                        {timing.showJoinMeeting && session.meeting_url && (
                                            <button
                                                onClick={() => window.open(session.meeting_url, '_blank')}
                                                className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-4 py-2 rounded-lg text-xs md:text-sm shadow-xs transition-all duration-200 flex items-center gap-1.5 cursor-pointer"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                                </svg>
                                                <span>Join Meeting</span>
                                            </button>
                                        )}

                                        {session.status !== 'cancelled' && (
                                            <button
                                                onClick={() => openAddMenteePanel(session.id)}
                                                className={`inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-2 rounded-lg border transition-colors cursor-pointer ${
                                                    isAddPanelOpen
                                                        ? 'bg-slate-100 border-slate-300 text-slate-700'
                                                        : 'bg-white border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-700 hover:bg-blue-50'
                                                }`}
                                            >
                                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                                                </svg>
                                                {isAddPanelOpen ? 'Close Panel' : 'Add Mentee'}
                                            </button>
                                        )}
                                    </div>

                                    {/* Add Mentee Panel */}
                                    {isAddPanelOpen && (
                                        <div className="border-t border-slate-100 pt-4 mt-1">
                                            <p className="text-xs font-semibold text-slate-700 mb-2">
                                                Invite a same-domain mentee to join this session
                                                {session.domain && (
                                                    <span className="ml-1 text-blue-600">(@{session.domain})</span>
                                                )}
                                            </p>

                                            {panelError && (
                                                <p className="text-xs text-rose-600 font-medium mb-2">{panelError}</p>
                                            )}

                                            {loadingMentees ? (
                                                <p className="text-xs text-slate-500">Loading eligible mentees...</p>
                                            ) : availableMentees.length === 0 ? (
                                                <p className="text-xs text-slate-500 italic">
                                                    No eligible same-domain mentees available to add.
                                                </p>
                                            ) : (
                                                <div className="space-y-2">
                                                    {availableMentees.map((m) => (
                                                        <div
                                                            key={m.id}
                                                            className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg px-3 py-2"
                                                        >
                                                            <div>
                                                                <p className="text-xs font-semibold text-slate-800">{m.name}</p>
                                                                <p className="text-xs text-slate-500">{m.email}</p>
                                                            </div>
                                                            <button
                                                                onClick={() => handleAddMentee(session.id, m.id)}
                                                                disabled={addingMenteeId === m.id}
                                                                className="text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg disabled:opacity-50 cursor-pointer transition-colors"
                                                            >
                                                                {addingMenteeId === m.id ? 'Adding...' : 'Invite'}
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )
                        })
                    )}
                </div>
            </div>
        </div>
    )
}

export default Sessions