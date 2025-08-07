export interface User {
  id: string;
  email: string;
  name: string;
  picture_url?: string;
  role: 'student' | 'teacher' | 'admin';
  created_at: string;
}

export interface Assignment {
  id: string;
  title: string;
  description?: string;
  subject: string;
  due_at: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface AssignmentLog {
  id: string;
  assignment_id: string;
  user_id: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'overdue';
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Event {
  id: string;
  title: string;
  description?: string;
  category: 'academic' | 'cultural' | 'sports' | 'administrative' | 'other';
  start_at: string;
  end_at: string;
  location?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}