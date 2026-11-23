export interface Job {
  _id: string
  source: string
  source_id: string
  title: string
  company: string
  url: string
  location: string
  tags: string[]
  job_type: string
  salary: string
  description: string
  published_at: string | null
  fetched_at: string
  remote: boolean
  latam_friendly: boolean
  score: number
  matched: boolean
  matched_keywords: string[]
  excluded_keywords: string[]
  seniority: string
  apply_type: string
  application_status: string
  notes: string
  age_days: number | null
}

export interface Stats {
  total: number
  latam_friendly: number
  by_source: Record<string, number>
  by_seniority: Record<string, number>
}

export interface MatchResult {
  score: number | null
  reasoning: string
  key_requirements: string[]
  matched_skills: string[]
  gaps: string[]
}

export function useApi() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  const fetchMatches = (params: Record<string, string | number | boolean> = {}) =>
    $fetch<{ count: number; jobs: Job[] }>(`${base}/matches`, { query: params })

  const fetchStats = () => $fetch<Stats>(`${base}/stats`)

  const matchJob = (id: string) =>
    $fetch<{ status: string; job_id: string; match?: MatchResult; detail?: string }>(
      `${base}/match/${id}`,
      { method: 'POST' },
    )

  const cvJob = (id: string) =>
    $fetch<{ status: string; job_id: string; cv?: string; detail?: string }>(
      `${base}/cv/${id}`,
      { method: 'POST' },
    )

  const updateApplication = (id: string, status: string, notes?: string) =>
    $fetch<{ status: string; detail?: string }>(`${base}/jobs/${id}/application`, {
      method: 'PATCH',
      body: { status, notes },
    })

  return { fetchMatches, fetchStats, matchJob, cvJob, updateApplication }
}
