import { useState } from 'react';
import { useAssignments } from '../hooks/useAssignments';
import { useAuth } from '../contexts/AuthContext';
import { format, isPast, isToday, isTomorrow } from 'date-fns';
import { Link } from 'react-router-dom';

export default function Assignments() {
  const { user } = useAuth();
  const [filter, setFilter] = useState<'all' | 'mine'>('mine');
  const [subjectFilter, setSubjectFilter] = useState<string>('');
  
  const { data: assignments, isLoading } = useAssignments({
    mine: filter === 'mine',
    subject: subjectFilter || undefined,
  });

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
        return 'text-red-600 bg-red-50 border-red-200';
      case 'due-today':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'due-tomorrow':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
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

  // Get unique subjects for filter
  const subjects = Array.from(
    new Set((assignments as any[])?.map((a: any) => a.subject) || [])
  );

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <div className="sm:flex sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Assignments</h1>
            <p className="mt-2 text-gray-600">
              Manage your assignments and track your progress
            </p>
          </div>
          {user?.role !== 'student' && (
            <div className="mt-4 sm:mt-0">
              <Link
                to="/assignments/create"
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                Create Assignment
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              View
            </label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as 'all' | 'mine')}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="mine">My Assignments</option>
              <option value="all">All Assignments</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subject
            </label>
            <select
              value={subjectFilter}
              onChange={(e) => setSubjectFilter(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">All Subjects</option>
              {subjects.map((subject) => (
                <option key={subject} value={subject}>
                  {subject}
                </option>
              ))}
            </select>
          </div>
          
          <div className="sm:flex sm:items-end">
            <button
              onClick={() => {
                setFilter('mine');
                setSubjectFilter('');
              }}
              className="w-full sm:w-auto inline-flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Assignments List */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading assignments...</p>
        </div>
      ) : assignments && (assignments as any[]).length > 0 ? (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {(assignments as any[]).map((assignment: any) => {
              const status = getAssignmentStatus(assignment.due_at);
              return (
                <li key={assignment.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-medium text-gray-900 truncate">
                            {assignment.title}
                          </h3>
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(status)}`}>
                            {getStatusText(status)}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                          <span className="font-medium">{assignment.subject}</span>
                          <span>•</span>
                          <span>Due: {format(new Date(assignment.due_at), 'MMM d, yyyy h:mm a')}</span>
                        </div>
                        {assignment.description && (
                          <p className="mt-2 text-sm text-gray-600">
                            {assignment.description}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <Link
                          to={`/assignments/${assignment.id}`}
                          className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                        >
                          View Details
                        </Link>
                        {user?.role !== 'student' && (
                          <Link
                            to={`/assignments/${assignment.id}/edit`}
                            className="inline-flex items-center px-3 py-1 border border-blue-300 rounded-md text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100"
                          >
                            Edit
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <div className="mx-auto h-12 w-12 text-gray-400">
            📝
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No assignments</h3>
          <p className="mt-1 text-sm text-gray-500">
            {filter === 'mine' 
              ? "You don't have any assignments yet."
              : "No assignments have been created yet."
            }
          </p>
          {user?.role !== 'student' && (
            <div className="mt-6">
              <Link
                to="/assignments/create"
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                Create First Assignment
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}