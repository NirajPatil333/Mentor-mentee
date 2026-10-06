import { useEffect, useState } from 'react'
import api from '../services/api'

function Requests() {
    const [requests, setRequests] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    const fetchRequests = async () => {
        try {
            const token = localStorage.getItem('token')

            const response = await api.get('/requests/received', {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            })

            setRequests(response.data.requests || [])
        } catch (err) {
            setError(
                err.response?.data?.message ||
                'Failed to load requests.'
            )
        } finally {
            setLoading(false)
        }
    }

    const handleAccept = async (requestId) => {
        try {
            const token = localStorage.getItem('token')

            await api.patch(
                `/requests/${requestId}/accept`,
                {},
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            )

            fetchRequests()
        } catch (err) {
            setError(
                err.response?.data?.message ||
                'Failed to accept request.'
            )
        }
    }

    const handleReject = async (requestId) => {
        try {
            const token = localStorage.getItem('token')

            await api.patch(
                `/requests/${requestId}/reject`,
                {},
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            )

            fetchRequests()
        } catch (err) {
            setError(
                err.response?.data?.message ||
                'Failed to reject request.'
            )
        }
    }

    useEffect(() => {
        fetchRequests()
    }, [])

    if (loading) {
        return <p>Loading requests...</p>
    }

    if (error) {
        return <p className="text-red-600">{error}</p>
    }

    return (
        <div>
            <h1 className="text-2xl font-bold">
                Mentorship Requests
            </h1>

            <p className="text-gray-500 mt-1">
                Manage requests from mentees.
            </p>

            <div className="mt-6 space-y-4">
                {requests.length === 0 ? (
                    <div className="bg-white rounded-lg p-6">
                        <p className="text-gray-500">
                            No mentorship requests yet.
                        </p>
                    </div>
                ) : (
                    requests.map((request) => (
                        <div
                            key={request.id}
                            className="bg-white rounded-lg p-6 shadow-sm"
                        >
                            <h2 className="text-lg font-semibold">
                                {request.mentee?.name || 'Mentee'}
                            </h2>

                            <p className="text-gray-600 mt-2">
                                {request.message || 'No message provided.'}
                            </p>

                            <p className="text-sm text-gray-500 mt-3">
                                Status: {request.status}
                            </p>

                            {request.status === 'pending' && (
                                <div className="flex gap-3 mt-4">
                                    <button
                                        onClick={() => handleAccept(request.id)}
                                        className="bg-green-600 text-white px-4 py-2 rounded-lg"
                                    >
                                        Accept
                                    </button>

                                    <button
                                        onClick={() => handleReject(request.id)}
                                        className="bg-red-600 text-white px-4 py-2 rounded-lg"
                                    >
                                        Reject
                                    </button>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}

export default Requests