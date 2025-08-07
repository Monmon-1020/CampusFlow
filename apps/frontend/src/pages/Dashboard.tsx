import { useAssignments } from '../hooks/useAssignments';
import { useEvents } from '../hooks/useEvents';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { format, isPast, isToday, isTomorrow } from 'date-fns';

export default function Dashboard() {
  const { user } = useAuth();
  const { data: assignments, isLoading: assignmentsLoading } = useAssignments({ 
    mine: true, 
    due_soon: true 
  });
  const { data: events, isLoading: eventsLoading } = useEvents({ week: true });

  const getAssignmentStatus = (dueDate: string) => {
    const due = new Date(dueDate);
    if (isPast(due)) return 'overdue';
    if (isToday(due)) return 'due-today';
    if (isTomorrow(due)) return 'due-tomorrow';
    return 'upcoming';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'overdue':
        return 'text-red-600 bg-red-50';
      case 'due-today':
        return 'text-orange-600 bg-orange-50';
      case 'due-tomorrow':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-blue-600 bg-blue-50';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'overdue':
        return 'Overdue';
      case 'due-today':
        return 'Due Today';
      case 'due-tomorrow':
        return 'Due Tomorrow';
      default:
        return 'Upcoming';
    }
  };

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.name}!
        </h1>
        <p className="mt-2 text-gray-600">
          Here's what's happening in your academic life
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Assignments Section */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">
                Upcoming Assignments
              </h2>
              <Link
                to="/assignments"
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                View all →
              </Link>
            </div>
            
            {assignmentsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-500">Loading assignments...</p>
              </div>
            ) : assignments && (assignments as any[]).length > 0 ? (
              <div className="space-y-4">
                {(assignments as any[]).slice(0, 5).map((assignment: any) => {
                  const status = getAssignmentStatus(assignment.due_at);
                  return (
                    <div
                      key={assignment.id}
                      className="border-l-4 border-blue-400 pl-4 py-2"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-sm font-medium text-gray-900">
                            {assignment.title}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {assignment.subject}
                          </p>
                        </div>
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status)}`}>
                          {getStatusText(status)}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">
                        Due: {format(new Date(assignment.due_at), 'MMM d, h:mm a')}
                      </p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">No upcoming assignments</p>
                <Link
                  to="/assignments"
                  className="mt-2 text-sm text-blue-600 hover:text-blue-500"
                >
                  View all assignments
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Events Section */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">
                This Week's Events
              </h2>
              <Link
                to="/events"
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                View all →
              </Link>
            </div>
            
            {eventsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-500">Loading events...</p>
              </div>
            ) : events && (events as any[]).length > 0 ? (
              <div className="space-y-4">
                {(events as any[]).slice(0, 5).map((event: any) => (
                  <div
                    key={event.id}
                    className="border-l-4 border-green-400 pl-4 py-2"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">
                          {event.title}
                        </h3>
                        <p className="text-sm text-gray-500 capitalize">
                          {event.category}
                        </p>
                        {event.location && (
                          <p className="text-xs text-gray-400">
                            📍 {event.location}
                          </p>
                        )}
                      </div>
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                      {format(new Date(event.start_at), 'MMM d, h:mm a')} - {format(new Date(event.end_at), 'h:mm a')}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">No events this week</p>
                <Link
                  to="/events"
                  className="mt-2 text-sm text-blue-600 hover:text-blue-500"
                >
                  View all events
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">📝</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Assignments
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {(assignments as any[])?.length || 0}
                </dd>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">📅</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Events This Week
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {(events as any[])?.length || 0}
                </dd>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">👤</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Your Role
                </dt>
                <dd className="text-lg font-medium text-gray-900 capitalize">
                  {user?.role}
                </dd>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}