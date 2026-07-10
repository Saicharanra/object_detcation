import React, { useState, useEffect, useRef } from 'react'
import { Eye, EyeOff, Tag, Sliders, Download } from 'lucide-react'

// Curated colors for different classes
const CLASS_COLORS = [
  'border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  'border-violet-500 bg-violet-500/10 text-violet-700 dark:text-violet-300',
  'border-amber-500 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  'border-rose-500 bg-rose-500/10 text-rose-700 dark:text-rose-300',
  'border-sky-500 bg-sky-500/10 text-sky-700 dark:text-sky-300',
  'border-indigo-500 bg-indigo-500/10 text-indigo-700 dark:text-indigo-300',
  'border-fuchsia-500 bg-fuchsia-500/10 text-fuchsia-700 dark:text-fuchsia-300',
  'border-teal-500 bg-teal-500/10 text-teal-700 dark:text-teal-300'
]

const getColorClass = (name) => {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % CLASS_COLORS.length
  return CLASS_COLORS[index]
}

export default function BoundingBoxViewer({ imageUrl, annotatedImageUrl, objects = [], processingTime }) {
  const [useAnnotated, setUseAnnotated] = useState(false)
  const [filterConf, setFilterConf] = useState(0.25)
  const [hoveredIndex, setHoveredIndex] = useState(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0, naturalWidth: 1, naturalHeight: 1 })
  const imageRef = useRef(null)

  const handleDownloadCrop = (imgUrl, bbox, name) => {
    const img = new Image()
    img.crossOrigin = 'anonymous' // Avoid canvas CORS issues with Supabase Storage URLs
    img.src = imgUrl
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      
      const { xmin, ymin, xmax, ymax } = bbox
      const width = xmax - xmin
      const height = ymax - ymin
      
      canvas.width = width
      canvas.height = height
      
      ctx.drawImage(img, xmin, ymin, width, height, 0, 0, width, height)
      
      try {
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
        const link = document.createElement('a')
        link.download = `${name.toLowerCase()}_crop_${Date.now()}.jpg`
        link.href = dataUrl
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (err) {
        console.error('Failed to crop image due to CORS or canvas issue:', err)
        alert('Could not download cropped object image. Ensure your browser doesn\'t block canvas modifications.')
      }
    }
    img.onerror = () => {
      console.error('Failed to load image for cropping:', imgUrl)
    }
  }

  const updateDimensions = () => {
    if (imageRef.current) {
      setDimensions({
        width: imageRef.current.clientWidth,
        height: imageRef.current.clientHeight,
        naturalWidth: imageRef.current.naturalWidth || 1,
        naturalHeight: imageRef.current.naturalHeight || 1
      })
    }
  }

  useEffect(() => {
    // Setup resize listener
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Filter objects based on confidence threshold
  const filteredObjects = objects.filter(obj => obj.confidence >= filterConf)

  // Scale boxes to match rendered image dimensions
  const scaleX = dimensions.width / dimensions.naturalWidth
  const scaleY = dimensions.height / dimensions.naturalHeight

  return (
    <div className="space-y-6">
      {/* Top Bar / Mode Selector */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-slate-50 dark:bg-darkCard/40 rounded-2xl border border-slate-200/50 dark:border-darkBorder/50">
        <div className="flex items-center space-x-3">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">View Mode:</span>
          <div className="inline-flex bg-slate-200/60 dark:bg-slate-950/40 p-1 rounded-xl">
            <button
              onClick={() => setUseAnnotated(false)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                !useAnnotated 
                  ? 'bg-white dark:bg-darkCard text-brand-600 dark:text-brand-400 shadow-sm' 
                  : 'text-slate-650 dark:text-slate-400 hover:text-slate-800'
              }`}
            >
              Interactive Overlay
            </button>
            {annotatedImageUrl && (
              <button
                onClick={() => setUseAnnotated(true)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                  useAnnotated 
                    ? 'bg-white dark:bg-darkCard text-brand-600 dark:text-brand-400 shadow-sm' 
                    : 'text-slate-650 dark:text-slate-400 hover:text-slate-800'
                }`}
              >
                Static Annotated
              </button>
            )}
          </div>
        </div>

        {processingTime && (
          <span className="text-xs font-semibold px-3 py-1.5 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 rounded-xl">
            Latency: {processingTime}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Image Display */}
        <div className="lg:col-span-2 flex flex-col items-center justify-center">
          <div className="relative w-full overflow-hidden rounded-2xl border border-slate-200 dark:border-darkBorder bg-slate-100 dark:bg-slate-950 flex justify-center items-center">
            {useAnnotated ? (
              <img
                src={annotatedImageUrl}
                alt="Annotated detection results"
                className="max-h-[500px] w-full object-contain"
              />
            ) : (
              <div className="relative inline-block max-w-full">
                <img
                  ref={imageRef}
                  src={imageUrl}
                  alt="Original upload"
                  onLoad={updateDimensions}
                  className="max-h-[500px] w-full object-contain block mx-auto"
                />

                {/* Render Bounding Boxes */}
                {dimensions.width > 0 &&
                  filteredObjects.map((obj, index) => {
                    const { xmin, ymin, xmax, ymax } = obj.bounding_box
                    const colorClass = getColorClass(obj.name)
                    const isHovered = hoveredIndex === index
                    
                    const left = xmin * scaleX
                    const top = ymin * scaleY
                    const width = (xmax - xmin) * scaleX
                    const height = (ymax - ymin) * scaleY

                    return (
                      <div
                        key={index}
                        onMouseEnter={() => setHoveredIndex(index)}
                        onMouseLeave={() => setHoveredIndex(null)}
                        className={`absolute border-2 rounded-sm transition-all duration-150 cursor-pointer ${
                          isHovered 
                            ? 'border-brand-500 scale-102 ring-2 ring-brand-500/20 z-20 shadow-glow-strong' 
                            : colorClass.split(' ')[0] + ' z-10'
                        }`}
                        style={{
                          left: `${left}px`,
                          top: `${top}px`,
                          width: `${width}px`,
                          height: `${height}px`,
                        }}
                      >
                        {/* Label Badge */}
                        <div
                          className={`absolute bottom-full left-0 mb-1 flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold shadow-md transition-colors whitespace-nowrap ${
                            isHovered
                              ? 'bg-brand-600 text-white'
                              : colorClass.split(' ').slice(1).join(' ')
                          }`}
                        >
                          <span>{obj.name}</span>
                          <span>{(obj.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    )
                  })}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Controls and Objects List */}
        <div className="space-y-4">
          {!useAnnotated && (
            <div className="glass-card p-5 space-y-4">
              <h3 className="text-sm font-semibold flex items-center space-x-1.5">
                <Sliders className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                <span>Filter Detections</span>
              </h3>
              
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-medium text-slate-700 dark:text-slate-300">
                  <span>Confidence Threshold</span>
                  <span className="font-semibold text-brand-600 dark:text-brand-400">{filterConf.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.95"
                  step="0.05"
                  value={filterConf}
                  onChange={(e) => setFilterConf(parseFloat(e.target.value))}
                  className="w-full accent-brand-500 cursor-pointer"
                />
              </div>
            </div>
          )}

          {/* List of Detected Objects */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-semibold flex items-center space-x-1.5">
                <Tag className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                <span>Objects Detected ({filteredObjects.length})</span>
              </h3>
            </div>

            {filteredObjects.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">
                <EyeOff className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <span>No objects match the current confidence filter.</span>
              </div>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {filteredObjects.map((obj, index) => {
                  const colorClass = getColorClass(obj.name)
                  const isHovered = hoveredIndex === index

                  return (
                    <div
                      key={index}
                      onMouseEnter={() => setHoveredIndex(index)}
                      onMouseLeave={() => setHoveredIndex(null)}
                      className={`flex items-center justify-between p-3 rounded-xl border transition-all duration-200 cursor-pointer ${
                        isHovered
                          ? 'border-brand-500 bg-brand-500/5 dark:bg-brand-500/10 shadow-sm translate-x-1'
                          : 'border-slate-200/50 hover:border-slate-300 dark:border-darkBorder/50 dark:hover:border-darkBorder bg-slate-50/50 dark:bg-darkCard/20'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5">
                        <span className={`w-3 h-3 rounded-full border-2 ${colorClass.split(' ')[0]}`} />
                        <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{obj.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold px-2 py-1 bg-slate-200/60 text-slate-700 dark:bg-slate-800 dark:text-slate-300 rounded-lg">
                          {(obj.confidence * 100).toFixed(0)}%
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDownloadCrop(imageUrl, obj.bounding_box, obj.name)
                          }}
                          title="Download cropped object image"
                          className="p-1 hover:bg-slate-250 dark:hover:bg-slate-800 text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 rounded-lg transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
