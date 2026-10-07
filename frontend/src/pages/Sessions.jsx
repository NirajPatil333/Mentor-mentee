import { useEffect, useState } from 'react'
import api from '../services/api'

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

    const token = localStorage.getItem('token')

    const fetchData = async () => {
        try {
            const headers = {
                Authorization: `Bearer ${token}`,
            }

            const requestsResponse = await api.get(
                '/requests/received',
                { headers }
            )

            const sessionsResponse = await api.get(
                '/sessions',
                { headers }
            )

            const acceptedRequests =
                (requestsResponse.data.requests || []).filter(
                    (request) => request.status === 'accepted'
                )

            setRequests(acceptedRequests)
            setSessions(sessionsResponse.data.sessions || [])
        } catch (err) {
            setError(
                err.response?.data?.message ||
                'Failed to load sessions.'
            )
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
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
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
            setError(
                err.response?.data?.message ||
                'Failed to create session.'
            )
        }
    }

    if (loading) {
        return <p>Loading sessions...</p>
    }

    return (
        <div>
            <h1 className="text-2xl font-bold">
                Sessions
            </h1>

            <p className="text-gray-500 mt-1">
                Schedule and manage mentorship sessions.
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

            {/* Schedule Session */}
            <div className="bg-white rounded-lg p-6 mt-6 shadow-sm">
                <h2 className="text-xl font-semibold">
                    Schedule Session
                </h2>

                <form
                    onSubmit={handleCreateSession}
                    className="mt-5 space-y-4"
                >
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Mentee
                        </label>

                        <select
                            value={requestId}
                            onChange={(e) => setRequestId(e.target.value)}
                            required
                            className="w-full border rounded-lg px-3 py-2"
                        >
                            <option value="">
                                Select mentee
                            </option>

                            {requests.map((request) => (
                                <option
                                    key={request.id}
                                    value={request.id}
                                >
                                    {request.mentee?.name || 'Mentee'}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Session Title
                        </label>

                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="e.g. React Learning Session"
                            required
                            className="w-full border rounded-lg px-3 py-2"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Description
                        </label>

                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="What will be discussed?"
                            className="w-full border rounded-lg px-3 py-2"
                            rows="3"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Date
                        </label>

                        <input
                            type="date"
                            value={scheduledDate}
                            onChange={(e) => setScheduledDate(e.target.value)}
                            required
                            className="border rounded-lg px-3 py-2"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">
                                Start Time
                            </label>

                            <input
                                type="time"
                                value={startTime}
                                onChange={(e) => setStartTime(e.target.value)}
                                required
                                className="w-full border rounded-lg px-3 py-2"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">
                                End Time
                            </label>

                            <input
                                type="time"
                                value={endTime}
                                onChange={(e) => setEndTime(e.target.value)}
                                required
                                className="w-full border rounded-lg px-3 py-2"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Schedule Session
                    </button>
                </form>
            </div>

            {/* Existing Sessions */}
            <div className="mt-8">
                <h2 className="text-xl font-semibold">
                    My Sessions
                </h2>

                <div className="mt-4 space-y-4">
                    {sessions.length === 0 ? (
                        <div className="bg-white rounded-lg p-6">
                            <p className="text-gray-500">
                                No sessions scheduled yet.
                            </p>
                        </div>
                    ) : (
                        sessions.map((session) => (
                            <div
                                key={session.id}
                                className="bg-white rounded-lg p-6 shadow-sm"
                            >
                                <h3 className="text-lg font-semibold">
                                    {session.title}
                                </h3>

                                <p className="text-gray-600 mt-2">
                                    {session.description}
                                </p>

                                <p className="text-sm text-gray-500 mt-3">
                                    Date: {session.scheduled_date}
                                </p>

                                <p className="text-sm text-gray-500">
                                    Time: {session.start_time} - {session.end_time}
                                </p>

                                <p className="text-sm mt-2">
                                    Status: {session.status}
                                </p>

                                {session.meeting_url && (
                                    <button
                                        onClick={() => window.open(session.meeting_url, '_blank')}
                                        className="mt-4 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                                    >
                                        Join Meeting
                                    </button>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}

export default Sessions