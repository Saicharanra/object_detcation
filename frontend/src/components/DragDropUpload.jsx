import React, { useState, useRef } from 'react'
import { Upload, X, Image as ImageIcon, Sliders, ChevronDown } from 'lucide-react'

export default function DragDropUpload({ onUpload, isLoading }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [prompt, setPrompt] = useState('')
  const [confidence, setConfidence] = useState(0.25)
  const [isDragActive, setIsDragActive] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true)
    } else if (e.type === 'dragleave') {
      setIsDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      validateAndSetFile(droppedFile)
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const validateAndSetFile = (selectedFile) => {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if (!validTypes.includes(selectedFile.type)) {
      alert('Invalid file format. Please upload JPG, JPEG, PNG, or WebP.')
      return
    }
    
    // Max size: 10MB
    if (selectedFile.size > 10 * 1024 * 1024) {
      alert('File size exceeds 10MB. Please upload a smaller image.')
      return
    }

    setFile(selectedFile)
    const reader = new FileReader()
    reader.onloadend = () => {
      setPreview(reader.result)
    }
    reader.readAsDataURL(selectedFile)
  }

  const handleClear = () => {
    setFile(null)
    setPreview('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!file) return
    onUpload({ file, prompt, confidence })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Upload Drag Area */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !file && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
          isDragActive 
            ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/20' 
            : 'border-slate-300 hover:border-brand-400 dark:border-darkBorder dark:hover:border-brand-500/50 bg-white/50 dark:bg-darkCard/50'
        } ${file ? 'cursor-default' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".jpg,.jpeg,.png,.webp"
          onChange={handleFileChange}
          disabled={isLoading}
        />

        {preview ? (
          <div className="relative inline-block max-w-full">
            <img
              src={preview}
              alt="Preview"
              className="max-h-72 object-contain rounded-xl mx-auto shadow-md"
            />
            {!isLoading && (
              <button
                type="button"
                onClick={handleClear}
                className="absolute -top-3 -right-3 p-1.5 bg-rose-500 hover:bg-rose-600 text-white rounded-full shadow-lg transition-transform hover:scale-110"
              >
                <X className="w-4.5 h-4.5" />
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center py-6">
            <div className="p-4 bg-brand-50 dark:bg-brand-950/30 rounded-2xl text-brand-600 dark:text-brand-400 mb-4 transition-transform hover:scale-105">
              <Upload className="w-8 h-8" />
            </div>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Drag & drop your image here, or{' '}
              <span className="text-brand-600 dark:text-brand-400 hover:underline">browse</span>
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Supports JPG, JPEG, PNG, or WebP up to 10MB
            </p>
          </div>
        )}
      </div>

      {/* Optional Custom Detection Prompts */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-slate-855 dark:text-slate-200">
          Detection Prompts (Optional)
        </label>
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. laptop, mobile phone, red bottle, keyboard"
          className="input-field"
          disabled={isLoading}
        />
        <p className="text-[11px] text-slate-500">
          Leave blank to use default classes. Separate multiple classes with commas.
        </p>
      </div>

      {/* Advanced Settings */}
      <div className="border border-slate-200/50 dark:border-darkBorder/50 rounded-xl overflow-hidden">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-darkCard/30 text-xs font-semibold text-slate-650 dark:text-slate-400 hover:bg-slate-100/50 dark:hover:bg-darkCard/50 transition-colors"
        >
          <span className="flex items-center space-x-1.5">
            <Sliders className="w-4 h-4" />
            <span>Advanced Parameters</span>
          </span>
          <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${showAdvanced ? 'rotate-180' : ''}`} />
        </button>

        {showAdvanced && (
          <div className="p-4 bg-white dark:bg-darkCard/20 space-y-4 border-t border-slate-200/50 dark:border-darkBorder/50">
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-medium text-slate-700 dark:text-slate-300">
                <span>Confidence Threshold</span>
                <span className="font-semibold text-brand-600 dark:text-brand-400">{confidence.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.95"
                step="0.05"
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full accent-brand-500 cursor-pointer"
                disabled={isLoading}
              />
              <p className="text-[10px] text-slate-500">
                Lower values show more objects; higher values ensure higher accuracy.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!file || isLoading}
        className="w-full btn-primary flex items-center justify-center space-x-2 py-3"
      >
        {isLoading ? (
          <>
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Analyzing Image...</span>
          </>
        ) : (
          <span>Run Object Detection</span>
        )}
      </button>
    </form>
  )
}
