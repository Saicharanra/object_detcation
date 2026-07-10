import React, { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  BarElement, 
  ArcElement, 
  Title, 
  Tooltip, 
  Legend, 
  Filler 
} from 'chart.js'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import { 
  BarChart3, 
  Sparkles, 
  Search, 
  Calendar, 
  Percent, 
  Download, 
  Layers, 
  Image as ImageIcon,
  ChevronRight,
  TrendingUp,
  Award,
  Cpu,
  Play,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  HelpCircle,
  Camera,
  VideoOff,
  Sliders
} from 'lucide-react'

import api from '../services/api'
import DragDropUpload from '../components/DragDropUpload'
import BoundingBoxViewer from '../components/BoundingBoxViewer'

// Register ChartJS modules
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

function LiveCameraStream({ useCustomModel }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const wsRef = useRef(null)
  const streamRef = useRef(null)
  
  const [streaming, setStreaming] = useState(false)
  const [loading, setLoading] = useState(false)
  const [prompt, setPrompt] = useState('')
  const [confidence, setConfidence] = useState(0.4)
  const [fps, setFps] = useState(0)
  const [latency, setLatency] = useState(0)
  const [detectedObjects, setDetectedObjects] = useState([])
  const [error, setError] = useState(null)

  // Use refs to avoid React closure capture in WebSocket callbacks
  const streamingRef = useRef(false)
  const promptRef = useRef(prompt)
  const confidenceRef = useRef(confidence)
  const useCustomModelRef = useRef(useCustomModel)

  useEffect(() => {
    promptRef.current = prompt
  }, [prompt])

  useEffect(() => {
    confidenceRef.current = confidence
  }, [confidence])

  useEffect(() => {
    useCustomModelRef.current = useCustomModel
  }, [useCustomModel])
  
  const startStream = async () => {
    setError(null)
    setLoading(true)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 }
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play().catch(e => console.error("Video element play error:", e))
      }
      
      const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${wsProto}//localhost:8000/ws/detect`
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws
      
      ws.onopen = () => {
        setStreaming(true)
        streamingRef.current = true
        setLoading(false)
        // Delay sending first frame slightly to allow camera warmth-up
        setTimeout(() => {
          if (ws.readyState === WebSocket.OPEN) {
            sendFrame(ws)
          }
        }, 300)
      }
      
      ws.onmessage = (event) => {
        try {
          const response = JSON.parse(event.data)
          if (response.error) {
            setError(response.error)
          } else {
            const img = new Image()
            img.src = response.image
            img.onload = () => {
              const canvas = canvasRef.current
              if (canvas) {
                const ctx = canvas.getContext('2d')
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
              }
            }
            
            setDetectedObjects(response.objects || [])
            setLatency(response.processing_time * 1000)
            trackFPS()
          }
        } catch (err) {
          console.error("WebSocket message error:", err)
        }
        
        if (streamingRef.current && ws.readyState === WebSocket.OPEN) {
          setTimeout(() => sendFrame(ws), 10)
        }
      }
      
      ws.onerror = (err) => {
        console.error("WebSocket error:", err)
        setError("WebSocket connection failed. Ensure backend server is running.")
        stopStream()
      }
      
      ws.onclose = () => {
        setStreaming(false)
        streamingRef.current = false
        setLoading(false)
      }
      
    } catch (err) {
      console.error("Camera access error:", err)
      setError("Failed to access camera. Please allow camera permissions in your browser.")
      setLoading(false)
    }
  }
  
  const stopStream = () => {
    setStreaming(false)
    streamingRef.current = false
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
      wsRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
    setDetectedObjects([])
    setFps(0)
    setLatency(0)
  }
  
  const sendFrame = (ws) => {
    const video = videoRef.current
    if (!video || !ws || ws.readyState !== WebSocket.OPEN || !streamRef.current || !streamingRef.current) return
    
    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = 640
    tempCanvas.height = 480
    const ctx = tempCanvas.getContext('2d')
    ctx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height)
    
    const dataUrl = tempCanvas.toDataURL('image/jpeg', 0.6)
    
    const payload = {
      image: dataUrl,
      prompt: promptRef.current,
      confidence: parseFloat(confidenceRef.current),
      use_custom_model: useCustomModelRef.current
    }
    ws.send(JSON.stringify(payload))
  }
  
  let lastFrameTime = useRef(performance.now())
  const trackFPS = () => {
    const now = performance.now()
    const currentFps = Math.round(1000 / (now - lastFrameTime.current))
    setFps(currentFps)
    lastFrameTime.current = now
  }
  
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Stream Display */}
      <div className="glass-card p-6 flex flex-col items-center justify-center relative overflow-hidden">
        <div className="flex items-center justify-between w-full mb-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Live Video Output</h3>
          
          {/* Status pill during active stream */}
          {streaming && (
            <div className="flex items-center space-x-4 text-[11px]">
              <div className="flex items-center space-x-1.5 px-2.5 py-0.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-full font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                <span>Live</span>
              </div>
              <span className="text-slate-500">Latency: <strong className="text-slate-700 dark:text-slate-350">{latency.toFixed(0)} ms</strong></span>
              <span className="text-slate-500">FPS: <strong className="text-slate-700 dark:text-slate-300">{fps}</strong></span>
            </div>
          )}
        </div>
        
        <div className="relative border-2 border-slate-200 dark:border-darkBorder rounded-2xl overflow-hidden bg-slate-950/90 aspect-[4/3] w-full max-w-[640px] flex items-center justify-center shadow-inner">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ position: 'absolute', width: '1px', height: '1px', opacity: 0 }}
          />
          <canvas
            ref={canvasRef}
            width={640}
            height={480}
            className={`w-full max-w-[640px] aspect-[4/3] object-cover ${streaming ? 'block' : 'hidden'}`}
          />
          
          {!streaming && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 space-y-4">
              <div className="p-4 bg-slate-800/80 rounded-full text-slate-400">
                <Camera className="w-10 h-10 animate-pulse" />
              </div>
              <span className="text-sm font-bold text-slate-300">Camera Feed Inactive</span>
              <p className="text-xs text-slate-500 max-w-xs leading-normal">
                Start the live camera stream to detect objects dynamically in real-time.
              </p>
              
              <button
                onClick={startStream}
                disabled={loading}
                className="btn-primary py-2.5 px-6 font-semibold shadow-md text-sm flex items-center justify-center space-x-2 rounded-xl transition-all hover:scale-102 mt-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4.5 h-4.5 animate-spin" />
                    <span>Connecting...</span>
                  </>
                ) : (
                  <>
                    <Camera className="w-4.5 h-4.5" />
                    <span>Start Camera Stream</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {error && (
          <div className="w-full mt-4 p-3 bg-red-50 dark:bg-red-950/15 rounded-xl border border-red-200/20 text-red-700 dark:text-red-400 text-xs leading-normal text-center">
            {error}
          </div>
        )}

        {streaming && (
          <div className="w-full mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-100 dark:border-darkBorder/30 pt-4 animate-fade-in">
            {/* Active detections list */}
            <div className="flex-1 space-y-1.5 w-full text-left">
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Active Detections</h4>
              {detectedObjects.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No objects currently detected.</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {detectedObjects.map((obj, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 bg-brand-500/10 text-brand-600 dark:text-brand-400 rounded-lg text-[11px] font-bold border border-brand-500/20"
                    >
                      {obj.name} ({(obj.confidence * 100).toFixed(0)}%)
                    </span>
                  ))}
                </div>
              )}
            </div>
            
            {/* Stop Stream Button */}
            <button
              onClick={stopStream}
              className="bg-rose-500 hover:bg-rose-600 text-white font-semibold py-2 px-4 rounded-xl shadow-sm text-xs transition-colors flex items-center justify-center space-x-1.5 w-full sm:w-auto self-end"
            >
              <VideoOff className="w-3.5 h-3.5" />
              <span>Stop Stream</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('studio')
  const [detectionResult, setDetectionResult] = useState(null)
  
  // Custom Model & Training States
  const [useCustomModel, setUseCustomModel] = useState(false)
  const [trainingEpochs, setTrainingEpochs] = useState(5)

  // Table Filters State
  const [searchName, setSearchName] = useState('')
  const [minConfFilter, setMinConfFilter] = useState(0.25)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // 1. Fetch Analytics data
  const { data: analyticsData, isLoading: isAnalyticsLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: async () => {
      const res = await api.get('/analytics')
      return res.data
    }
  })

  // 2. Fetch history for the search table (default gets everything, filters are done client-side for immediate response)
  const { data: historyData, isLoading: isHistoryLoading } = useQuery({
    queryKey: ['history-all'],
    queryFn: async () => {
      const res = await api.get('/history', { params: { limit: 100 } })
      return res.data
    }
  })

  // Fetch training status (polls when job is active)
  const { data: statusData, refetch: refetchStatus } = useQuery({
    queryKey: ['training-status'],
    queryFn: async () => {
      const res = await api.get('/train/status')
      return res.data
    },
    refetchInterval: (query) => {
      const status = query.state.data?.latest_job?.status
      return (status === 'pending' || status === 'training') ? 5000 : false
    }
  })

  // Fetch training classes eligibility
  const { data: classesData, refetch: refetchClasses } = useQuery({
    queryKey: ['training-classes'],
    queryFn: async () => {
      const res = await api.get('/train/classes')
      return res.data
    }
  })

  // 3. Mutation to upload and run detection
  const detectMutation = useMutation({
    mutationFn: async ({ file, prompt, confidence }) => {
      const formData = new FormData()
      formData.append('file', file)
      if (prompt) formData.append('prompt', prompt)
      if (confidence) formData.append('confidence', confidence)
      if (useCustomModel) formData.append('use_custom_model', 'true')
      
      const res = await api.post('/detect', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return res.data
    },
    onSuccess: (data) => {
      setDetectionResult(data)
      // Invalidate queries to refresh stats and history logs
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      queryClient.invalidateQueries({ queryKey: ['history-all'] })
      queryClient.invalidateQueries({ queryKey: ['training-classes'] })
    }
  })

  // Training mutation
  const trainMutation = useMutation({
    mutationFn: async (epochs) => {
      const formData = new FormData()
      formData.append('epochs', epochs)
      const res = await api.post('/train', formData)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-status'] })
      queryClient.invalidateQueries({ queryKey: ['training-classes'] })
    }
  })

  const handleUploadSubmit = ({ file, prompt, confidence }) => {
    detectMutation.mutate({ file, prompt, confidence })
  }

  // Filter Table Data
  const getFilteredDetections = () => {
    if (!historyData?.history) return []
    
    let allDetections = []
    historyData.history.forEach(item => {
      item.detections.forEach(det => {
        allDetections.push({
          ...det,
          image_id: item.image_id,
          original_filename: item.original_filename,
          uploaded_at: item.uploaded_at,
          image_url: item.image_url
        })
      })
    })

    return allDetections.filter(det => {
      const matchesSearch = searchName ? det.name.toLowerCase().includes(searchName.toLowerCase()) : true
      const matchesConf = det.confidence >= minConfFilter
      
      let matchesDate = true
      if (startDate || endDate) {
        const uploadDate = new Date(det.uploaded_at)
        if (startDate && uploadDate < new Date(startDate)) matchesDate = false
        if (endDate) {
          const end = new Date(endDate)
          end.setHours(23, 59, 59, 999) // include whole day
          if (uploadDate > end) matchesDate = false
        }
      }
      
      return matchesSearch && matchesConf && matchesDate
    })
  }

  const filteredDetections = getFilteredDetections()

  // Export to CSV Function
  const exportToCSV = () => {
    if (filteredDetections.length === 0) return
    
    const headers = ['Image Filename', 'Object Name', 'Confidence', 'Xmin', 'Ymin', 'Xmax', 'Ymax', 'Prompt Used', 'Processing Latency', 'Detected At']
    const rows = filteredDetections.map(det => [
      `"${det.original_filename}"`,
      `"${det.name}"`,
      det.confidence,
      det.bounding_box.xmin.toFixed(1),
      det.bounding_box.ymin.toFixed(1),
      det.bounding_box.xmax.toFixed(1),
      det.bounding_box.ymax.toFixed(1),
      `"${det.prompt_used || 'Default'}"`,
      `"${det.processing_time}"`,
      new Date(det.uploaded_at).toLocaleString()
    ])

    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(','), ...rows.map(e => e.join(','))].join('\n')
      
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement("a")
    link.setAttribute("href", encodedUri)
    link.setAttribute("download", `yolo_world_detections_${new Date().toISOString().split('T')[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Chart Configurations
  const renderCharts = () => {
    if (isAnalyticsLoading || !analyticsData) return null

    // 1. Upload Activity (Line Chart)
    const activityLabels = analyticsData.upload_activity.map(a => {
      const d = new Date(a.date)
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    })
    const activityData = {
      labels: activityLabels,
      datasets: [{
        label: 'Uploads',
        data: analyticsData.upload_activity.map(a => a.uploads),
        fill: true,
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.05)',
        tension: 0.4,
        pointBackgroundColor: '#8b5cf6',
      }]
    }

    // 2. Top Objects (Doughnut Chart)
    const topObjectsData = {
      labels: analyticsData.top_objects.map(o => o.name),
      datasets: [{
        data: analyticsData.top_objects.map(o => o.count),
        backgroundColor: [
          '#8b5cf6', '#6d28d9', '#a78bfa', '#c4b5fd', 
          '#10b981', '#f59e0b', '#ef4444', '#06b6d4', 
          '#3b82f6', '#64748b'
        ],
        borderWidth: 0,
      }]
    }

    // 3. Confidence Distribution (Bar Chart)
    const confData = {
      labels: Object.keys(analyticsData.confidence_distribution),
      datasets: [{
        label: 'Detections',
        data: Object.values(analyticsData.confidence_distribution),
        backgroundColor: '#a78bfa',
        hoverBackgroundColor: '#8b5cf6',
        borderRadius: 8,
      }]
    }

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          grid: { color: 'rgba(148, 163, 184, 0.1)' },
          ticks: { color: '#64748b', font: { size: 10 } }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#64748b', font: { size: 10 } }
        }
      }
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Upload Activity Line Chart */}
        <div className="glass-card p-5 flex flex-col h-80">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Upload Activity (Last 14 Days)</h4>
            <TrendingUp className="w-4 h-4 text-brand-650" />
          </div>
          <div className="flex-1 relative">
            <Line data={activityData} options={chartOptions} />
          </div>
        </div>

        {/* Confidence Distribution Bar Chart */}
        <div className="glass-card p-5 flex flex-col h-80">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Confidence Bins</h4>
            <Percent className="w-4 h-4 text-brand-650" />
          </div>
          <div className="flex-1 relative">
            <Bar data={confData} options={chartOptions} />
          </div>
        </div>

        {/* Top Detected Objects Doughnut Chart */}
        <div className="glass-card p-5 flex flex-col h-80 md:col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Top Detected Items</h4>
            <Layers className="w-4 h-4 text-brand-650" />
          </div>
          <div className="flex-1 relative flex items-center justify-center">
            {analyticsData.top_objects.length === 0 ? (
              <span className="text-slate-500 text-xs">No data available</span>
            ) : (
              <div className="w-full h-full max-h-56">
                <Doughnut 
                  data={topObjectsData} 
                  options={{
                    ...chartOptions,
                    plugins: {
                      legend: {
                        display: true,
                        position: 'right',
                        labels: { boxWidth: 10, font: { size: 9 }, color: '#64748b' }
                      }
                    }
                  }} 
                />
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Welcome Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center space-x-2">
            <Sparkles className="w-8 h-8 text-brand-500 animate-pulse-slow" />
            <span>Detection Studio</span>
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Detect objects in real-time using open vocabulary YOLO-World.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex bg-slate-100 dark:bg-slate-900/60 p-1.5 rounded-2xl self-start sm:self-center space-x-1">
          <button
            onClick={() => setActiveTab('studio')}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${
              activeTab === 'studio'
                ? 'bg-white dark:bg-darkCard text-brand-600 dark:text-brand-400 shadow-sm'
                : 'text-slate-655 dark:text-slate-400 hover:text-slate-950'
            }`}
          >
            Detection Studio
          </button>
          <button
            onClick={() => setActiveTab('live')}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${
              activeTab === 'live'
                ? 'bg-white dark:bg-darkCard text-brand-600 dark:text-brand-400 shadow-sm'
                : 'text-slate-655 dark:text-slate-400 hover:text-slate-950'
            }`}
          >
            Live Camera
          </button>
          <button
            onClick={() => setActiveTab('training')}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${
              activeTab === 'training'
                ? 'bg-white dark:bg-darkCard text-brand-600 dark:text-brand-400 shadow-sm'
                : 'text-slate-655 dark:text-slate-400 hover:text-slate-950'
            }`}
          >
            Model Training
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${
              activeTab === 'analytics'
                ? 'bg-white dark:bg-darkCard text-brand-600 dark:text-brand-400 shadow-sm'
                : 'text-slate-655 dark:text-slate-400 hover:text-slate-950'
            }`}
          >
            Analytics Dashboard
          </button>
        </div>
      </div>

      {activeTab === 'studio' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form Upload Panel */}
          <div className="glass-card p-6 h-fit lg:col-span-1">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Analyze Image</h2>
              
              {statusData?.custom_model_available && (
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="sr-only peer" 
                    checked={useCustomModel} 
                    onChange={(e) => setUseCustomModel(e.target.checked)} 
                  />
                  <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-750 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-slate-600 peer-checked:bg-brand-600"></div>
                  <span className="ml-2 text-xs font-bold text-slate-600 dark:text-slate-350">Custom Model</span>
                </label>
              )}
            </div>
            <DragDropUpload onUpload={handleUploadSubmit} isLoading={detectMutation.isPending} />
          </div>

          {/* Results Visualizer Panel */}
          <div className="lg:col-span-2">
            {detectionResult ? (
              <div className="glass-card p-6 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200/50 dark:border-darkBorder/50">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">Detection Result</h2>
                  <span className="text-xs text-slate-500 font-medium">ID: {detectionResult.image_id.substring(0, 8)}...</span>
                </div>
                <BoundingBoxViewer
                  imageUrl={detectionResult.original_image_url}
                  annotatedImageUrl={detectionResult.annotated_image_url}
                  objects={detectionResult.objects}
                  processingTime={detectionResult.processing_time}
                />
              </div>
            ) : (
              <div className="glass-card p-12 border-2 border-dashed border-slate-200 dark:border-darkBorder flex flex-col items-center justify-center text-center h-[500px]">
                <div className="p-4 bg-slate-100 dark:bg-darkCard rounded-full text-slate-400 mb-4">
                  <ImageIcon className="w-12 h-12" />
                </div>
                <h3 className="text-base font-bold text-slate-805 dark:text-slate-350">Awaiting Image Analysis</h3>
                <p className="text-slate-500 text-xs max-w-sm mt-2">
                  Upload an image on the left, optionally enter custom labels, and hit detect. Results will display interactively here.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'live' && (
        <LiveCameraStream useCustomModel={useCustomModel} />
      )}

      {activeTab === 'analytics' && (
        /* Analytics Page */
        <div className="space-y-8">
          {/* Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="glass-card p-6 flex items-center space-x-4">
              <div className="p-3 bg-brand-50 text-brand-650 dark:bg-brand-950/20 dark:text-brand-400 rounded-2xl">
                <ImageIcon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-500">Total Uploaded Images</p>
                <h3 className="text-2xl font-bold mt-1 text-slate-850 dark:text-slate-100">
                  {isAnalyticsLoading ? '...' : analyticsData?.summary?.total_images ?? 0}
                </h3>
              </div>
            </div>

            <div className="glass-card p-6 flex items-center space-x-4">
              <div className="p-3 bg-indigo-50 text-indigo-650 dark:bg-indigo-950/20 dark:text-indigo-400 rounded-2xl">
                <BarChart3 className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-500">Total Bounding Boxes</p>
                <h3 className="text-2xl font-bold mt-1 text-slate-850 dark:text-slate-100">
                  {isAnalyticsLoading ? '...' : analyticsData?.summary?.total_detections ?? 0}
                </h3>
              </div>
            </div>

            <div className="glass-card p-6 flex items-center space-x-4">
              <div className="p-3 bg-emerald-50 text-emerald-650 dark:bg-emerald-950/20 dark:text-emerald-400 rounded-2xl">
                <Award className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-500">Most Detected Object</p>
                <h3 className="text-2xl font-bold mt-1 text-slate-850 dark:text-slate-100 truncate max-w-[200px]">
                  {isAnalyticsLoading ? '...' : analyticsData?.summary?.most_detected_object ?? 'None'}
                </h3>
              </div>
            </div>
          </div>

          {/* Render Graph Charts */}
          {renderCharts()}

          {/* Table Filters Log Section */}
          <div className="glass-card p-6 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Detection Records Log</h3>
              
              <button
                onClick={exportToCSV}
                disabled={filteredDetections.length === 0}
                className="btn-secondary flex items-center space-x-2 text-xs py-2 px-4 shadow-sm"
              >
                <Download className="w-4 h-4" />
                <span>Export CSV ({filteredDetections.length})</span>
              </button>
            </div>

            {/* Filter controls bar */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 bg-slate-50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-200/50 dark:border-darkBorder/50">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1">
                  <Search className="w-3.5 h-3.5" />
                  <span>Object Name</span>
                </label>
                <input
                  type="text"
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                  placeholder="Filter name..."
                  className="input-field py-1.5 px-3 text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1">
                  <Percent className="w-3.5 h-3.5" />
                  <span>Min Confidence</span>
                </label>
                <select
                  value={minConfFilter}
                  onChange={(e) => setMinConfFilter(parseFloat(e.target.value))}
                  className="input-field py-1.5 px-3 text-xs"
                >
                  <option value={0.1}>10% or higher</option>
                  <option value={0.25}>25% or higher</option>
                  <option value={0.5}>50% or higher</option>
                  <option value={0.75}>75% or higher</option>
                  <option value={0.9}>90% or higher</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Start Date</span>
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="input-field py-1.5 px-3 text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>End Date</span>
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="input-field py-1.5 px-3 text-xs"
                />
              </div>
            </div>

            {/* Filtered Detections Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-darkBorder text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    <th className="py-3 px-4">Image Target</th>
                    <th className="py-3 px-4">Detected Object</th>
                    <th className="py-3 px-4 text-center">Confidence</th>
                    <th className="py-3 px-4">Coordinates (xyxy)</th>
                    <th className="py-3 px-4">Detected At</th>
                    <th className="py-3 px-4 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-darkBorder/40 text-xs text-slate-700 dark:text-slate-350">
                  {isHistoryLoading ? (
                    <tr>
                      <td colSpan="6" className="text-center py-8">Loading logs...</td>
                    </tr>
                  ) : filteredDetections.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center py-8 text-slate-500">No detection matches found with active filters.</td>
                    </tr>
                  ) : (
                    filteredDetections.slice(0, 15).map((det, index) => (
                      <tr key={index} className="hover:bg-slate-50/50 dark:hover:bg-darkCard/10 transition-colors">
                        <td className="py-3.5 px-4 font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[180px]">
                          {det.original_filename}
                        </td>
                        <td className="py-3.5 px-4 font-bold text-brand-600 dark:text-brand-450">{det.name}</td>
                        <td className="py-3.5 px-4 text-center font-bold">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] ${
                            det.confidence >= 0.75 
                              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400' 
                              : det.confidence >= 0.5 
                              ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400'
                              : 'bg-slate-100 text-slate-650 dark:bg-slate-800 dark:text-slate-400'
                          }`}>
                            {(det.confidence * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-[10px] text-slate-400">
                          {`[${det.bounding_box.xmin.toFixed(0)}, ${det.bounding_box.ymin.toFixed(0)}, ${det.bounding_box.xmax.toFixed(0)}, ${det.bounding_box.ymax.toFixed(0)}]`}
                        </td>
                        <td className="py-3.5 px-4 text-slate-500">
                          {new Date(det.uploaded_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <a 
                            href={det.image_url} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="inline-flex items-center space-x-1 text-[11px] font-bold text-brand-500 hover:text-brand-650"
                          >
                            <span>Open</span>
                            <ChevronRight className="w-3.5 h-3.5" />
                          </a>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              {filteredDetections.length > 15 && (
                <p className="text-[10px] text-slate-500 text-right mt-3">
                  Showing top 15 records. Download CSV to export all {filteredDetections.length} matches.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Model Training Studio */}
      {activeTab === 'training' && (
        <div className="space-y-8 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Status Column */}
            <div className="glass-card p-6 h-fit space-y-6 lg:col-span-1">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-brand-500" />
                <span>Model Status</span>
              </h2>

              <div className="p-4 bg-slate-50 dark:bg-slate-950/40 rounded-2xl border border-slate-200/50 dark:border-darkBorder/50 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Fine-Tuned Model:</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                    statusData?.custom_model_available
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400'
                      : 'bg-slate-100 text-slate-550 dark:bg-slate-800 dark:text-slate-400'
                  }`}>
                    {statusData?.custom_model_available ? 'Available' : 'Not Active'}
                  </span>
                </div>

                {statusData?.custom_model_available && statusData?.trained_classes && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Trained Objects:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {statusData.trained_classes.map((cls, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-brand-50 dark:bg-brand-950/20 text-brand-700 dark:text-brand-400 rounded-md text-[10px] font-semibold">
                          {cls}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Training config form */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-655 dark:text-slate-350">Training Epochs</label>
                  <select
                    value={trainingEpochs}
                    onChange={(e) => setTrainingEpochs(parseInt(e.target.value))}
                    disabled={trainMutation.isPending || (statusData?.latest_job?.status === 'pending' || statusData?.latest_job?.status === 'training')}
                    className="input-field py-2 px-3 text-sm"
                  >
                    <option value={3}>3 Epochs (Fastest)</option>
                    <option value={5}>5 Epochs (Standard)</option>
                    <option value={10}>10 Epochs (Better)</option>
                    <option value={20}>20 Epochs (Recommended)</option>
                    <option value={30}>30 Epochs (Thorough)</option>
                    <option value={50}>50 Epochs (High Accuracy)</option>
                  </select>
                  <p className="text-[10px] text-slate-500 leading-normal">
                    Fewer epochs complete faster. Training runs locally on the server CPU.
                  </p>
                </div>

                <button
                  onClick={() => trainMutation.mutate(trainingEpochs)}
                  disabled={
                    !classesData?.can_train ||
                    trainMutation.isPending ||
                    (statusData?.latest_job?.status === 'pending' || statusData?.latest_job?.status === 'training')
                  }
                  className="w-full btn-primary py-2.5 flex items-center justify-center space-x-2 shadow-sm text-sm font-semibold"
                >
                  {trainMutation.isPending || (statusData?.latest_job?.status === 'pending' || statusData?.latest_job?.status === 'training') ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Training Model...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      <span>Start Fine-Tuning</span>
                    </>
                  )}
                </button>

                {!classesData?.can_train && (
                  <div className="p-3 bg-amber-50 dark:bg-amber-950/10 rounded-xl border border-amber-250/20 text-amber-800 dark:text-amber-450 text-[11px] leading-normal flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 animate-pulse" />
                    <span>
                      You need at least <strong>{classesData?.min_images_required || 3} annotated images</strong> to start training.
                      Current annotated images: <strong>{classesData?.images_count ?? 0}</strong>.
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column (Classes & History) */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Training Job Status Card */}
              {statusData?.latest_job && (
                <div className="glass-card p-6 space-y-4">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">Latest Training Run</h3>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-200/50 dark:border-darkBorder/50">
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Status</span>
                      <div className="flex items-center space-x-1.5 mt-0.5">
                        {(statusData.latest_job.status === 'pending' || statusData.latest_job.status === 'training') && (
                          <RefreshCw className="w-3.5 h-3.5 text-brand-500 animate-spin" />
                        )}
                        {statusData.latest_job.status === 'completed' && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                        )}
                        {statusData.latest_job.status === 'failed' && (
                          <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                        )}
                        <span className="text-xs font-bold capitalize text-slate-700 dark:text-slate-350">
                          {statusData.latest_job.status}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Epochs</span>
                      <p className="text-xs font-bold text-slate-700 dark:text-slate-350 mt-0.5">{statusData.latest_job.epochs}</p>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Started At</span>
                      <p className="text-xs text-slate-655 dark:text-slate-455 mt-0.5">
                        {new Date(statusData.latest_job.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {(statusData.latest_job.status === 'pending' || statusData.latest_job.status === 'training') && (
                    <div className="p-4 bg-brand-50/50 dark:bg-brand-950/10 rounded-xl border border-brand-200/20 text-brand-800 dark:text-brand-400 text-xs leading-normal flex items-start space-x-2">
                      <RefreshCw className="w-4 h-4 animate-spin flex-shrink-0 mt-0.5" />
                      <span>
                        The system is compiling your annotations and running training. Do not close this tab or restart the server. 
                        Progress updates every 5 seconds.
                      </span>
                    </div>
                  )}

                  {statusData.latest_job.status === 'failed' && (
                    <div className="p-4 bg-red-50 dark:bg-red-950/10 rounded-xl border border-red-200/20 text-red-800 dark:text-red-400 text-xs leading-normal space-y-1">
                      <p className="font-bold">Error Details:</p>
                      <p className="font-mono text-[11px] bg-white dark:bg-darkCard p-2.5 rounded-lg border border-red-100 dark:border-darkBorder/50 overflow-x-auto">
                        {statusData.latest_job.error_message}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Dataset classes layout */}
              <div className="glass-card p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">Dataset Summary</h3>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                    {classesData?.images_count ?? 0} Images Available
                  </span>
                </div>

                <div className="space-y-4">
                  <p className="text-xs text-slate-500 leading-normal">
                    The model will be trained to detect the following custom items based on your upload history. 
                    Adding more images and labeling various objects helps the model learn better.
                  </p>

                  {classesData?.classes && classesData.classes.length > 0 ? (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {classesData.classes.map((cls, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-950/40 rounded-xl border border-slate-200/50 dark:border-darkBorder/50 flex flex-col justify-between hover:border-slate-350 transition-colors">
                          <span className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">{cls}</span>
                          <span className="text-[9px] text-slate-450 mt-1 uppercase font-semibold">Custom Label</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center bg-slate-50 dark:bg-slate-950/20 rounded-xl border border-slate-200/50 dark:border-darkBorder/50">
                      <span className="text-xs text-slate-500">No classes detected in your history yet.</span>
                    </div>
                  )}
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  )
}
