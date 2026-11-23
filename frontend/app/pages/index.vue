<script setup lang="ts">
const api = useApi()

const seniority = ref('')
const source = ref('')
const search = ref('')

const stats = ref<Stats | null>(null)
const jobs = ref<Job[]>([])
const loading = ref(false)
const error = ref('')

const seniorityOptions = ['', 'junior', 'mid', 'senior', 'unknown']
const seniorityLabels: Record<string, string> = {
  '': 'Todas',
  junior: 'Junior',
  mid: 'Mid',
  senior: 'Senior',
  unknown: 'Sin definir',
}

const seniorityClass: Record<string, string> = {
  junior: 'badge--junior',
  mid: 'badge--mid',
  senior: 'badge--senior',
  unknown: 'badge--unknown',
}

const applicationStatuses = [
  { value: 'not_applied', label: 'No aplicada' },
  { value: 'saved', label: 'Guardada' },
  { value: 'applied', label: 'Aplicada' },
  { value: 'follow_up', label: 'Follow-up' },
  { value: 'interview', label: 'Entrevista' },
  { value: 'offer', label: 'Oferta' },
  { value: 'rejected', label: 'Rechazada' },
  { value: 'not_interested', label: 'No me interesa' },
]

async function setStatus(job: Job, status: string) {
  try {
    await api.updateApplication(job._id, status)
    job.application_status = status
  } catch {}
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    stats.value = await api.fetchStats()
    const params: Record<string, string | number | boolean> = { limit: 200 }
    if (seniority.value) params.seniority = seniority.value
    if (source.value) params.source = source.value
    const res = await api.fetchMatches(params)
    jobs.value = res.jobs
  } catch {
    error.value = 'No pude conectar con el API. ¿Está corriendo? Ejecuta `make up` primero.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const filteredJobs = computed(() => {
  if (!search.value) return jobs.value
  const q = search.value.toLowerCase()
  return jobs.value.filter((j) =>
    [j.title, j.company, ...j.tags, ...j.matched_keywords]
      .join(' ')
      .toLowerCase()
      .includes(q),
  )
})

const sources = computed(() => (stats.value ? Object.keys(stats.value.by_source) : []))

function open(url: string) {
  if (url) window.open(url, '_blank')
}

function formatSalary(s: string) {
  return s || 'Sin salario'
}

const currencyRe = /[\$\€\£\¥]/

function hasCurrency(s: string) {
  return currencyRe.test(s)
}

const modal = ref<null | { type: 'match' | 'cv'; job: Job }>(null)
const modalLoading = ref(false)
const modalError = ref('')
const matchResult = ref<MatchResult | null>(null)
const cvText = ref('')

async function showMatch(job: Job) {
  modal.value = { type: 'match', job }
  modalLoading.value = true
  modalError.value = ''
  matchResult.value = null
  cvText.value = ''
  try {
    const res = await api.matchJob(job._id)
    if (res.status === 'ok' && res.match) {
      matchResult.value = res.match
    } else {
      modalError.value = res.detail || 'No se pudo evaluar la vacante.'
    }
  } catch {
    modalError.value = 'Error al conectar con el API.'
  } finally {
    modalLoading.value = false
  }
}

async function showCv(job: Job) {
  modal.value = { type: 'cv', job }
  modalLoading.value = true
  modalError.value = ''
  matchResult.value = null
  cvText.value = ''
  try {
    const res = await api.cvJob(job._id)
    if (res.status === 'ok' && res.cv) {
      cvText.value = res.cv
    } else {
      modalError.value = res.detail || 'No se pudo generar el CV.'
    }
  } catch {
    modalError.value = 'Error al conectar con el API.'
  } finally {
    modalLoading.value = false
  }
}

function closeModal() {
  modal.value = null
  modalLoading.value = false
  modalError.value = ''
  matchResult.value = null
  cvText.value = ''
}

function scoreClass(score: number | null) {
  if (score === null) return ''
  if (score >= 70) return 'score--high'
  if (score >= 40) return 'score--mid'
  return 'score--low'
}

async function copyCv() {
  try {
    await navigator.clipboard.writeText(cvText.value)
  } catch {}
}
</script>

<template>
  <main class="container">
    <header class="header">
      <h1>Job Hunter</h1>
      <p class="subtitle">Vacantes remotas aptas desde Colombia</p>
      <button class="btn" :disabled="loading" @click="load">
        {{ loading ? 'Cargando…' : 'Refrescar' }}
      </button>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="stats" class="stats">
      <div class="stat">
        <span class="stat__num">{{ stats.total }}</span>
        <span class="stat__label">Vacantes</span>
      </div>
      <div class="stat">
        <span class="stat__num">{{ stats.latam_friendly }}</span>
        <span class="stat__label">Aptas LATAM</span>
      </div>
      <div class="stat" v-for="(n, s) in stats.by_seniority" :key="s">
        <span class="stat__num">{{ n }}</span>
        <span class="stat__label">{{ seniorityLabels[s] ?? s }}</span>
      </div>
    </section>

    <section class="filters">
      <select v-model="seniority" @change="load">
        <option v-for="o in seniorityOptions" :key="o" :value="o">
          Senioridad: {{ seniorityLabels[o] }}
        </option>
      </select>
      <select v-model="source" @change="load">
        <option value="">Fuente: Todas</option>
        <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
      </select>
      <input v-model="search" type="search" placeholder="Buscar por título, empresa o keyword" />
    </section>

    <p class="count">{{ filteredJobs.length }} resultados</p>

    <ul class="jobs">
      <li v-for="job in filteredJobs" :key="job._id" class="job">
        <div class="job__top">
          <span class="badge badge--source">{{ job.source }}</span>
          <span class="badge badge--apply">{{ job.apply_type }}</span>
          <span class="badge" :class="seniorityClass[job.seniority]">
            {{ seniorityLabels[job.seniority] ?? job.seniority }}
          </span>
          <span class="badge badge--score">score {{ job.score }}</span>
          <span v-if="job.remote" class="badge badge--remote">remoto</span>
          <span v-if="job.age_days !== null" class="badge badge--age">{{ job.age_days }}d</span>
        </div>
        <h2 class="job__title">{{ job.title }}</h2>
        <p class="job__company">{{ job.company }}</p>
        <p class="job__meta">
          <span v-if="job.location">{{ job.location }}</span>
          <span v-if="job.salary" class="job__salary">
            {{ formatSalary(job.salary) }}
            <span v-if="!hasCurrency(job.salary)" class="salary-note">(sin moneda/periodo)</span>
          </span>
          <span v-if="job.job_type">{{ job.job_type }}</span>
        </p>
        <div class="job__tags">
          <span v-for="k in job.matched_keywords" :key="k" class="chip">{{ k }}</span>
        </div>
        <div class="job__actions">
          <select
            class="status-select"
            :value="job.application_status"
            @change="setStatus(job, ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="s in applicationStatuses" :key="s.value" :value="s.value">
              {{ s.label }}
            </option>
          </select>
          <a class="btn btn--small" :href="job.url" target="_blank" rel="noopener">Aplicar ↗</a>
          <button class="btn btn--small btn--ghost" @click="showMatch(job)">Match</button>
          <button class="btn btn--small btn--ghost" @click="showCv(job)">CV</button>
        </div>
      </li>
    </ul>

    <p v-if="!loading && filteredJobs.length === 0" class="empty">
      Sin resultados para estos filtros.
    </p>

    <div v-if="modal" class="modal" @click.self="closeModal">
      <div class="modal__panel">
        <div class="modal__head">
          <h3>{{ modal.job.title }}</h3>
          <button class="modal__close" @click="closeModal">✕</button>
        </div>
        <p class="modal__company">{{ modal.job.company }}</p>

        <p v-if="modalLoading" class="modal__loading">Consultando al LLM…</p>
        <p v-if="modalError" class="error">{{ modalError }}</p>

        <template v-if="modal.type === 'match' && matchResult">
          <div class="match-score" :class="scoreClass(matchResult.score)">
            <span class="match-score__num">{{ matchResult.score ?? '—' }}</span>
            <span class="match-score__label">/ 100</span>
          </div>
          <p class="match-reasoning">{{ matchResult.reasoning }}</p>

          <h4>Requisitos clave</h4>
          <ul class="modal__list">
            <li v-for="r in matchResult.key_requirements" :key="r">{{ r }}</li>
          </ul>

          <h4>Skills que encajan</h4>
          <div class="job__tags">
            <span v-for="s in matchResult.matched_skills" :key="s" class="chip chip--good">{{ s }}</span>
          </div>

          <h4>Gaps</h4>
          <ul class="modal__list modal__list--bad">
            <li v-for="g in matchResult.gaps" :key="g">{{ g }}</li>
          </ul>
        </template>

        <template v-if="modal.type === 'cv' && cvText">
          <pre class="cv">{{ cvText }}</pre>
          <button class="btn btn--small" @click="copyCv">Copiar CV</button>
        </template>
      </div>
    </div>
  </main>
</template>
