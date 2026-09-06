export interface Option {
  value: number;
  label: string;
}

export interface Question {
  id: string;
  text: string;
  options: Option[];
}

export interface StartResponse {
  session_id: string;
  question: Question;
  question_number: number;
  total_max_questions: number;
}

export interface DepartmentMatch {
  id: string;
  name: string;
  probability: number;
}

export interface TraitScore {
  trait: string;
  score: number;
}

export interface Explanation {
  what_youll_do: string[];
  skills_gained: string[];
  strongest_traits: string[];
}

export interface Result {
  recommended_department: DepartmentMatch;
  runner_up: DepartmentMatch;
  top_matches: DepartmentMatch[];
  probabilities: Record<string, number>;
  top_traits: TraitScore[];
  explanation: Explanation;
}

export interface AnswerResponse {
  completed: boolean;
  question?: Question;
  question_number?: number;
  total_max_questions?: number;
  result?: Result;
}

export interface StatusResponse {
  session_id: string;
  questions_answered: number;
  max_questions: number;
  current_top_department: string | null;
  current_probability: number | null;
  completed: boolean;
  progress_percentage: number;
}

export interface Department {
  id: string;
  name: string;
  description: string;
}

export interface DepartmentDetail extends Department {
  weights: Record<string, number>;
  responsibilities: string[];
  skills: string[];
}

export interface SimilarDepartment {
  id: string;
  name: string;
  similarity: number;
}
