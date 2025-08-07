import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';

export function useAssignments(params?: {
  mine?: boolean;
  subject?: string;
  due_soon?: boolean;
}) {
  return useQuery({
    queryKey: ['assignments', params],
    queryFn: () => apiClient.getAssignments(params),
  });
}

export function useAssignment(id: string) {
  return useQuery({
    queryKey: ['assignments', id],
    queryFn: () => apiClient.getAssignment(id),
    enabled: !!id,
  });
}

export function useCreateAssignment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: any) => apiClient.createAssignment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
}

export function useUpdateAssignment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      apiClient.updateAssignment(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      queryClient.invalidateQueries({ queryKey: ['assignments', id] });
    },
  });
}

export function useDeleteAssignment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => apiClient.deleteAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
}

export function useAssignmentLogs(assignmentId?: string) {
  return useQuery({
    queryKey: ['assignment-logs', assignmentId],
    queryFn: () => apiClient.getAssignmentLogs(assignmentId),
  });
}

export function useCreateAssignmentLog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: any) => apiClient.createAssignmentLog(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignment-logs'] });
    },
  });
}

export function useUpdateAssignmentLog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      apiClient.updateAssignmentLog(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignment-logs'] });
    },
  });
}