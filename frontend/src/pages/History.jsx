import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Calendar, ChevronLeft, ChevronRight, Trash2, Eye, CalendarDays, Hourglass, ShieldAlert } from 'lucide-react'
import api from '../services/api'
import BoundingBoxViewer from '../components/BoundingBoxViewer'

export default function History() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [selectedItem, setSelectedItem] = useState(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState(null)
  
  const limit = 9
  const offset = page * limit

  // 1. Query paginated detection history
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['history', page, search],
    queryFn: async () => {
      const res = await api.get('/history', {
        params: { limit, offset, search: search || undefined }
      })
      return res.data
    }
  })

  // 2. Mutation to delete history item
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const res = await api.delete(`/history/${id}`)
      return res.data
    },
    onSuccess: () => {
      setDeleteConfirmId(null)
      setSelectedItem(null)
      // Refresh historical logs and stats
      queryClient.invalidateQueries({ queryKey: ['history'] })
      queryClient.invalidateQueries({ queryKey: ['history-all'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
    }
  })

  const handleSearchChange = (e) => {
    setSearch(e.target.value)
    setPage(0) // reset page on search
  }

  const handleDelete = (id) => {
    deleteMutation.mutate(id)
  }

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Detection History</h1>
          <p className="text-slate-500 text-sm mt-1">Browse, inspect, and manage your past object detection uploads.</p>
        </div>

        {/* Search Input */}
        <div className="relative max-w-sm w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={handleSearchChange}
            placeholder="Search by detected object..."
            className="input-field pl-10 py-2.5 text-sm"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="glass-card p-4 h-80 animate-pulse bg-slate-100/50 dark:bg-darkCard/20 border border-slate-200/50 dark:border-darkBorder/50 rounded-2xl" />
          ))}
        </div>
      ) : !data?.history || data.history.length === 0 ? (
        <div className="glass-card p-12 text-center max-w-lg mx-auto py-16">
          <ShieldAlert className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-350">No Detections Found</h3>
          <p className="text-slate-500 text-xs mt-2">
            {search ? "No records match your query. Try searching for something else." : "You haven't run any object detections yet. Go to the dashboard to start."}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Grid list of runs */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.history.map((item) => {
              const dateObj = new Date(item.uploaded_at)
              const displayDate = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
              const uniqueObjects = [...new Set(item.detections.map(d => d.name))]

              return (
                <div 
                  key={item.image_id} 
                  className="glass-card p-4 flex flex-col justify-between group hover:shadow-glow dark:hover:border-brand-500/30 transition-all duration-300"
                >
                  <div className="space-y-3">
                    {/* Image Preview Container */}
                    <div className="relative h-44 rounded-xl overflow-hidden bg-slate-150 dark:bg-slate-950 flex items-center justify-center border border-slate-200/50 dark:border-darkBorder/30">
                      <img 
                        src={item.annotated_image_url || item.image_url} 
                        alt={item.original_filename} 
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-3">
                        <button
                          onClick={() => setSelectedItem(item)}
                          className="w-full flex items-center justify-center space-x-1.5 bg-white text-slate-900 py-2 rounded-xl text-xs font-bold shadow-md hover:bg-brand-50 transition-colors"
                        >
                          <Eye className="w-4 h-4 text-brand-650" />
                          <span>View Details</span>
                        </button>
                      </div>
                    </div>

                    {/* Meta info */}
                    <div className="space-y-1">
                      <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200 truncate" title={item.original_filename}>
                        {item.original_filename}
                      </h4>
                      <div className="flex items-center space-x-3 text-[11px] text-slate-500 font-semibold">
                        <span className="flex items-center space-x-1">
                          <CalendarDays className="w-3.5 h-3.5" />
                          <span>{displayDate}</span>
                        </span>
                        {item.detections.length > 0 && (
                          <span className="flex items-center space-x-1">
                            <Hourglass className="w-3.5 h-3.5" />
                            <span>{item.detections[0].processing_time}</span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Detected tags */}
                    <div className="flex flex-wrap gap-1.5 max-h-12 overflow-hidden">
                      {uniqueObjects.length === 0 ? (
                        <span className="text-[10px] text-slate-400">No objects detected</span>
                      ) : (
                        uniqueObjects.slice(0, 4).map((name, i) => (
                          <span key={i} className="text-[10px] font-bold px-2 py-0.5 bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-350 rounded-md">
                            {name}
                          </span>
                        ))
                      )}
                      {uniqueObjects.length > 4 && (
                        <span className="text-[10px] font-bold px-2 py-0.5 bg-brand-50 text-brand-600 dark:bg-brand-950/40 dark:text-brand-400 rounded-md">
                          +{uniqueObjects.length - 4} more
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions footer */}
                  <div className="flex justify-between items-center border-t border-slate-100 dark:border-darkBorder/40 mt-4 pt-3.5">
                    <button
                      onClick={() => setSelectedItem(item)}
                      className="text-xs font-bold text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-350 transition-colors"
                    >
                      Inspect Bounding Boxes
                    </button>
                    <button
                      onClick={() => setDeleteConfirmId(item.image_id)}
                      className="text-rose-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/20 p-2 rounded-xl transition-colors"
                      title="Delete detection history"
                    >
                      <Trash2 className="w-4.5 h-4.5" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Pagination controls */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center bg-white dark:bg-darkCard p-4 rounded-2xl border border-slate-200/50 dark:border-darkBorder/50 transition-colors">
              <button
                disabled={page === 0}
                onClick={() => setPage(page - 1)}
                className="btn-secondary flex items-center space-x-1 text-xs py-2 px-3"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Previous</span>
              </button>
              
              <span className="text-xs text-slate-500 font-semibold">
                Page {page + 1} of {totalPages}
              </span>

              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage(page + 1)}
                className="btn-secondary flex items-center space-x-1 text-xs py-2 px-3"
              >
                <span>Next</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Modal - Inspection Overlay */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="relative glass-card p-6 w-full max-w-5xl bg-white dark:bg-darkBg max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-200/50 dark:border-darkBorder/50 pb-3.5 mb-6">
              <div>
                <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                  {selectedItem.original_filename}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Uploaded at {new Date(selectedItem.uploaded_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-darkBorder text-slate-500 hover:bg-slate-50 dark:hover:bg-darkCard text-xs font-bold"
              >
                Close
              </button>
            </div>

            <BoundingBoxViewer
              imageUrl={selectedItem.image_url}
              annotatedImageUrl={selectedItem.annotated_image_url}
              objects={selectedItem.detections}
              processingTime={selectedItem.detections[0]?.processing_time}
            />
          </div>
        </div>
      )}

      {/* Modal - Delete Confirmation */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="glass-card p-6 w-full max-w-md bg-white dark:bg-darkBg text-center shadow-xl">
            <div className="p-3 bg-rose-50 text-rose-600 dark:bg-rose-950/20 dark:text-rose-400 rounded-full w-fit mx-auto mb-4">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">Delete Item?</h3>
            <p className="text-slate-500 text-xs mt-2">
              This action will permanently delete this record, including its annotations and files in storage. This cannot be undone.
            </p>
            <div className="flex items-center space-x-3 mt-6">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="flex-1 btn-secondary py-2.5"
                disabled={deleteMutation.isPending}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirmId)}
                className="flex-1 bg-rose-600 hover:bg-rose-700 text-white font-semibold py-2.5 rounded-xl transition-colors active:scale-98 disabled:opacity-50"
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
