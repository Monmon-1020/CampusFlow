import { useState } from 'react';
import { useEvents, useEventCategories } from '../hooks/useEvents';
import { useAuth } from '../contexts/AuthContext';
import { format, startOfWeek, endOfWeek, addWeeks, subWeeks } from 'date-fns';
import { Link } from 'react-router-dom';

export default function Events() {
  const { user } = useAuth();
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [viewMode, setViewMode] = useState<'week' | 'all'>('week');
  
  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 });
  
  const { data: events, isLoading } = useEvents({
    week: viewMode === 'week',
    category: categoryFilter || undefined,
    start_date: viewMode === 'week' ? weekStart.toISOString() : undefined,
    end_date: viewMode === 'week' ? weekEnd.toISOString() : undefined,
  });
  
  const { data: categories } = useEventCategories();

  const getCategoryColor = (category: string) => {
    const colors = {
      academic: 'text-blue-600 bg-blue-50 border-blue-200',
      cultural: 'text-purple-600 bg-purple-50 border-purple-200',
      sports: 'text-green-600 bg-green-50 border-green-200',
      administrative: 'text-gray-600 bg-gray-50 border-gray-200',
      other: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    };
    return colors[category as keyof typeof colors] || colors.other;
  };

  const getCategoryIcon = (category: string) => {
    const icons = {
      academic: '📚',
      cultural: '🎭',
      sports: '⚽',
      administrative: '📋',
      other: '📌',
    };
    return icons[category as keyof typeof icons] || icons.other;
  };

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <div className="sm:flex sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Events</h1>
            <p className="mt-2 text-gray-600">
              Stay up to date with school events and activities
            </p>
          </div>
          {user?.role === 'admin' && (
            <div className="mt-4 sm:mt-0">
              <Link
                to="/events/create"
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
              >
                Create Event
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Filters and Navigation */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              View
            </label>
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as 'week' | 'all')}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
            >
              <option value="week">This Week</option>
              <option value="all">All Events</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
            >
              <option value="">All Categories</option>
              {categories?.map((category) => (
                <option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {viewMode === 'week' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Week Navigation
              </label>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentWeek(subWeeks(currentWeek, 1))}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  ← Prev
                </button>
                <button
                  onClick={() => setCurrentWeek(addWeeks(currentWeek, 1))}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
          
          <div className="sm:flex sm:items-end">
            <button
              onClick={() => {
                setViewMode('week');
                setCategoryFilter('');
                setCurrentWeek(new Date());
              }}
              className="w-full sm:w-auto inline-flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Reset
            </button>
          </div>
        </div>

        {viewMode === 'week' && (
          <div className="mt-4 text-sm text-gray-600">
            Showing events for week of {format(weekStart, 'MMM d')} - {format(weekEnd, 'MMM d, yyyy')}
          </div>
        )}
      </div>

      {/* Events List */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading events...</p>
        </div>
      ) : events && (events as any[]).length > 0 ? (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {(events as any[]).map((event: any) => (
              <li key={event.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">
                          {getCategoryIcon(event.category)}
                        </span>
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {event.title}
                          </h3>
                          <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getCategoryColor(event.category)}`}>
                              {event.category.charAt(0).toUpperCase() + event.category.slice(1)}
                            </span>
                            <span>
                              {format(new Date(event.start_at), 'MMM d, yyyy h:mm a')} - {format(new Date(event.end_at), 'h:mm a')}
                            </span>
                          </div>
                          {event.location && (
                            <div className="mt-1 text-sm text-gray-500">
                              📍 {event.location}
                            </div>
                          )}
                          {event.description && (
                            <p className="mt-2 text-sm text-gray-600">
                              {event.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/events/${event.id}`}
                        className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                      >
                        View Details
                      </Link>
                      {user?.role === 'admin' && (
                        <Link
                          to={`/events/${event.id}/edit`}
                          className="inline-flex items-center px-3 py-1 border border-green-300 rounded-md text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100"
                        >
                          Edit
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <div className="mx-auto h-12 w-12 text-gray-400">
            📅
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No events</h3>
          <p className="mt-1 text-sm text-gray-500">
            {viewMode === 'week' 
              ? "No events scheduled for this week."
              : "No events have been created yet."
            }
          </p>
          {user?.role === 'admin' && (
            <div className="mt-6">
              <Link
                to="/events/create"
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
              >
                Create First Event
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}