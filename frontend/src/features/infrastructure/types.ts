export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Institution {
  id: string;
  name: string;
  code: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InstitutionInput {
  name?: string;
  code?: string;
  timezone?: string;
  is_active?: boolean;
}

export interface Classroom {
  id: string;
  institution: { id: string; code: string; name: string };
  code: string;
  name: string;
  capacity: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClassroomInput {
  code?: string;
  name?: string;
  capacity?: number | null;
  is_active?: boolean;
}

export interface Camera {
  id: string;
  code: string;
  display_name: string;
  classroom_id: string;
  classroom: { id: string; code: string; name: string };
  source_type: "LOCAL_FILE";
  status: "ACTIVE" | "INACTIVE";
  resolution: string | null;
  frame_rate: number | null;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface CameraInput {
  code?: string;
  display_name?: string;
  classroom_id?: string;
  source_type?: "LOCAL_FILE";
  status?: "ACTIVE" | "INACTIVE";
  resolution?: string | null;
  frame_rate?: number | null;
  description?: string | null;
}
