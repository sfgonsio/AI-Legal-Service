/**
 * WebSocket hook for real-time deposition assistant
 */
import { useEffect, useRef, useState, useCallback } from 'react'

export const useWebSocket = (sessionId, onMessage) => {
  const wsRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!sessionId) return

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${window.location.host}/api/deposition/ws/${sessionId}`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
      setError(null)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (onMessage) {
          onMessage(data)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      setError('Connection error')
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
    }

    wsRef.current = ws

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [sessionId, onMessage])

  const send = useCallback((message) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [isConnected])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
  }, [])

  return { isConnected, error, send, disconnect }
}
