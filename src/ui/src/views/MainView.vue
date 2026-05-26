<template>
  <div class="main-wrapper">

    <!-- 상단 티커 바 -->
    <header class="ticker-bar">
      <div class="ticker-track">
        <div class="ticker-inner">
          <span class="ticker-item" v-for="(item, i) in tickerItems.concat(tickerItems)" :key="i">
            <span class="ticker-name">{{ item.name }}</span>
            <span class="ticker-value">{{ item.value }}</span>
            <span :class="['ticker-change', item.change > 0 ? 'up' : 'down']">
              {{ item.change > 0 ? '▲' : '▼' }} {{ Math.abs(item.change) }}%
            </span>
            <span class="ticker-divider">|</span>
          </span>
        </div>
      </div>
    </header>

    <div class="body-wrapper">

      <div class="overlay" v-if="sidebarOpen" @click="sidebarOpen = false"></div>

      <button class="menu-btn" @click="sidebarOpen = !sidebarOpen">
        <span :class="['hamburger', { open: sidebarOpen }]">
          <span></span><span></span><span></span>
        </span>
      </button>

      <aside :class="['sidebar', { open: sidebarOpen }]">
        <div class="sidebar-header">
          <div class="sidebar-logo">
            <span class="logo-icon">📈</span>
            <span class="logo-text">StockAI</span>
          </div>
          <button class="sidebar-close" @click="sidebarOpen = false">✕</button>
        </div>
        <div class="sidebar-user">
          <div class="user-avatar">{{ userInitial }}</div>
          <div>
            <p class="user-name">{{ username }}</p>
            <p class="user-role">일반 회원</p>
          </div>
        </div>
        <nav class="sidebar-nav">
          <p class="nav-section-label">메뉴</p>
          <button :class="['nav-item', { active: currentTab === 'recommend' }]"
            @click="currentTab = 'recommend'; sidebarOpen = false">
            <span>🏆</span> 주식 추천
          </button>
          <button :class="['nav-item', { active: currentTab === 'news' }]"
            @click="currentTab = 'news'; sidebarOpen = false">
            <span>📰</span> 뉴스
          </button>
          <button :class="['nav-item', { active: currentTab === 'portfolio' }]"
            @click="currentTab = 'portfolio'; sidebarOpen = false">
            <span>💼</span> 포트폴리오
            <span v-if="portfolio.length > 0" class="nav-badge">{{ portfolio.length }}</span>
          </button>
        </nav>
        <button class="logout-btn" @click="handleLogout">로그아웃</button>
      </aside>

      <main class="content">

        <!-- 주식 추천 탭 -->
        <div v-if="currentTab === 'recommend'">
          <div class="page-header">
            <h2 class="page-title">오늘의 주식 추천</h2>
            <p class="page-sub">LS증권 뉴스 기반 AI 분석 결과</p>
          </div>
          <div class="two-col">
            <div class="col-left">
              <div class="summary-cards">
                <div class="summary-card">
                  <p class="card-label">추천 종목</p>
                  <p class="card-value">{{ recommendedStocks.length }}<span class="card-unit">개</span></p>
                </div>
                <div class="summary-card">
                  <p class="card-label">핵심 테마</p>
                  <p class="card-value">{{ topThemesCount }}<span class="card-unit">개</span></p>
                </div>
                <div class="summary-card">
                  <p class="card-label">업데이트</p>
                  <p class="card-value updated">{{ analysisUpdatedAt }}</p>
                </div>
              </div>
              <p class="section-title">추천 종목</p>
              <div class="stock-list">
                <div class="stock-card" v-for="stock in recommendedStocks" :key="stock.code" @click="goToDetail(stock.code)" style="cursor:pointer">
                <div class="stock-rank">{{ stock.rank }}</div>
                  <div class="stock-info">
                    <span class="stock-name">{{ stock.name }}</span>
                    <span class="stock-code">{{ stock.code }}</span>
                  </div>
                  <div class="stock-sparkline">
                    <svg width="60" height="28" viewBox="0 0 60 28">
                      <polyline :points="stock.sparkline" fill="none"
                        :stroke="stock.change > 0 ? '#ef4444' : '#2563eb'"
                        stroke-width="1.5" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <div class="stock-right">
                    <p class="stock-price">{{ stock.price }}</p>
                    <p :class="['stock-change', stock.change > 0 ? 'up' : 'down']">
                      {{ stock.change > 0 ? '▲' : '▼' }} {{ Math.abs(stock.change) }}%
                    </p>
                  </div>
                  <button class="bookmark-btn" @click="addToPortfolio(stock)"
                    :class="{ bookmarked: isBookmarked(stock.code) }"
                    :title="isBookmarked(stock.code) ? '포트폴리오에서 제거' : '포트폴리오에 추가'">
                    {{ isBookmarked(stock.code) ? '★' : '☆' }}
                  </button>
                </div>
              </div>
            </div>
            <div class="col-right">
              <div class="market-card">
                <div class="market-card-header">
                  <div>
                    <span class="market-badge kospi">KOSPI</span>
                    <p class="market-value">{{ kospiDisplay.value }}</p>
                    <p :class="['market-change', kospiDisplay.isUp ? 'up' : 'down']">{{ kospiDisplay.drate }}</p>
                  </div>
                  <svg width="100" height="50" viewBox="0 0 100 50" class="market-chart">
                    <defs>
                      <linearGradient id="kospiGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#ef4444" stop-opacity="0.2"/>
                        <stop offset="100%" stop-color="#ef4444" stop-opacity="0"/>
                      </linearGradient>
                    </defs>
                    <polygon points="0,40 10,35 20,38 30,28 40,30 50,22 60,25 70,15 80,18 90,10 100,8 100,50 0,50" fill="url(#kospiGrad)"/>
                    <polyline points="0,40 10,35 20,38 30,28 40,30 50,22 60,25 70,15 80,18 90,10 100,8"
                      fill="none" stroke="#ef4444" stroke-width="2" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="market-news-list">
                  <p class="news-section-label">주요 뉴스</p>
                  <div class="market-news-item" v-for="n in kospiNews" :key="n.id">
                    <span class="news-dot red"></span><span>{{ n.title }}</span>
                  </div>
                </div>
              </div>
              <div class="market-card">
                <div class="market-card-header">
                  <div>
                    <span class="market-badge kosdaq">KOSDAQ</span>
                    <p class="market-value">{{ kosdaqDisplay.value }}</p>
                    <p :class="['market-change', kosdaqDisplay.isUp ? 'up' : 'down']">{{ kosdaqDisplay.drate }}</p>
                  </div>
                  <svg width="100" height="50" viewBox="0 0 100 50" class="market-chart">
                    <defs>
                      <linearGradient id="kosdaqGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#16a34a" stop-opacity="0.2"/>
                        <stop offset="100%" stop-color="#16a34a" stop-opacity="0"/>
                      </linearGradient>
                    </defs>
                    <polygon points="0,45 10,40 20,42 30,35 40,32 50,28 60,20 70,22 80,12 90,8 100,5 100,50 0,50" fill="url(#kosdaqGrad)"/>
                    <polyline points="0,45 10,40 20,42 30,35 40,32 50,28 60,20 70,22 80,12 90,8 100,5"
                      fill="none" stroke="#16a34a" stroke-width="2" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="market-news-list">
                  <p class="news-section-label">주요 뉴스</p>
                  <div class="market-news-item" v-for="n in kosdaqNews" :key="n.id">
                    <span class="news-dot green"></span><span>{{ n.title }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 뉴스 탭 -->
        <div v-if="currentTab === 'news'">
          <div class="page-header">
            <h2 class="page-title">최신 뉴스</h2>
            <p class="page-sub">LS증권 뉴스 API 실시간 데이터</p>
          </div>
          <div class="news-list" v-if="newsList.length > 0">
            <div class="news-card" v-for="news in newsList" :key="news.id">
              <div class="news-tag">{{ news.tag }}</div>
              <p class="news-title">{{ news.title }}</p>
              <p class="news-time">{{ news.time }}</p>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>📰</p>
            <p>뉴스 데이터를 불러오는 중입니다</p>
            <p class="empty-sub">AI 분석이 완료되면 자동으로 표시됩니다</p>
          </div>
        </div>

        <!-- 포트폴리오 탭 -->
        <div v-if="currentTab === 'portfolio'">
          <div class="page-header">
            <h2 class="page-title">내 포트폴리오</h2>
            <p class="page-sub">관심 종목 즐겨찾기 관리</p>
          </div>

          <!-- 검색창 -->
          <div class="search-box">
            <input
              v-model="searchQuery"
              @input="onSearchInput"
              type="text"
              placeholder="종목명 또는 종목코드 검색 (예: 삼성전자, 005930)"
              class="search-input"
            />
            <span class="search-icon">🔍</span>

            <!-- 검색 결과 드롭다운 -->
            <div class="search-dropdown" v-if="searchResults.length > 0">
              <div class="search-result-item" v-for="result in searchResults" :key="result.code"
                @click="addToPortfolio(result)">
                <div>
                  <p class="result-name">{{ result.name }}</p>
                  <p class="result-code">{{ result.code }}</p>
                </div>
                <div class="result-right">
                  <p class="result-price">{{ result.price }}</p>
                  <p :class="['result-change', result.change > 0 ? 'up' : 'down']">
                    {{ result.change > 0 ? '▲' : '▼' }} {{ Math.abs(result.change) }}%
                  </p>
                </div>
                <button class="add-btn" :class="{ added: isBookmarked(result.code) }">
                  {{ isBookmarked(result.code) ? '✓ 추가됨' : '+ 추가' }}
                </button>
              </div>
            </div>

            <!-- 검색어 있는데 결과 없을 때 -->
            <div class="search-dropdown" v-if="searchQuery.length > 0 && searchResults.length === 0 && !searchLoading">
              <p class="no-result">검색 결과가 없습니다</p>
            </div>
          </div>

          <!-- API 상태 알림 -->
          <div v-if="apiMessage" :class="['api-message', apiMessageType]">
            {{ apiMessage }}
          </div>

          <!-- 포트폴리오 목록 -->
          <div v-if="portfolio.length > 0">
            <p class="section-title">즐겨찾기 종목 ({{ portfolio.length }})</p>
            <div class="portfolio-list">
              <div class="portfolio-card" v-for="stock in portfolio" :key="stock.code">
                <div class="portfolio-info">
                  <div class="stock-rank" style="background:#f0fdf4; color:#16a34a;">★</div>
                  <div>
                    <p class="stock-name">{{ stock.name }}</p>
                    <p class="stock-code">{{ stock.code }}</p>
                  </div>
                </div>
                <div class="portfolio-price">
                  <p class="stock-price">{{ stock.price }}</p>
                  <p :class="['stock-change', stock.change > 0 ? 'up' : 'down']">
                    {{ stock.change > 0 ? '▲' : '▼' }} {{ Math.abs(stock.change) }}%
                  </p>
                </div>
                <button class="remove-btn" @click="removeFromPortfolio(stock.code)">✕ 제거</button>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <p>⭐</p>
            <p>즐겨찾기한 종목이 없습니다</p>
            <p class="empty-sub">위 검색창에서 종목을 검색해 추가해보세요</p>
          </div>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
const router = useRouter()

function goToDetail(code) {
  router.push(`/stock/${code}`)
}

const BASE_URL = 'http://localhost:8080'

const currentTab = ref('recommend')

const topThemesCount = ref('-')
const analysisUpdatedAt = ref('로딩 중')

function timeAgo(dateStr) {
  if (!dateStr) return '-'
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (diff < 60) return '방금'
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
  return `${Math.floor(diff / 86400)}일 전`
}
const sidebarOpen = ref(false)
const username = ref(localStorage.getItem('username') || '사용자')
const userId = ref(localStorage.getItem('user_id') || '')
const userInitial = computed(() => username.value.charAt(0))

// ── 검색 ──
const searchQuery = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
let searchTimer = null

// 검색 입력 디바운스 (0.4초 후 실행)
function onSearchInput() {
  clearTimeout(searchTimer)
  searchResults.value = []
  if (searchQuery.value.trim().length === 0) return
  searchTimer = setTimeout(() => searchStocks(), 400)
}

async function searchStocks() {
  searchLoading.value = true
  try {
    // TODO: 백엔드 검색 API 연동
    // GET /stocks/search?query=삼성전자
    // const res = await axios.get(`${BASE_URL}/stocks/search`, {
    //   params: { query: searchQuery.value }
    // })
    // searchResults.value = res.data

    // 더미 검색 결과 (백엔드 완성 전 임시)
    const dummy = [
      { name: '삼성전자', code: '005930', price: '71,500원', change: 2.3 },
      { name: 'SK하이닉스', code: '000660', price: '138,000원', change: 1.8 },
      { name: 'NAVER', code: '035420', price: '182,500원', change: -0.5 },
      { name: '카카오', code: '035720', price: '42,300원', change: 0.9 },
      { name: 'LG에너지솔루션', code: '373220', price: '312,000원', change: -1.2 },
      { name: '현대차', code: '005380', price: '215,000원', change: 0.4 },
      { name: '삼성바이오로직스', code: '207940', price: '850,000원', change: -0.8 },
    ]
    searchResults.value = dummy.filter(s =>
      s.name.includes(searchQuery.value) || s.code.includes(searchQuery.value)
    )
  } finally {
    searchLoading.value = false
  }
}

// ── 포트폴리오 ──
const portfolio = ref([])
const apiMessage = ref('')
const apiMessageType = ref('success')

function isBookmarked(code) {
  return portfolio.value.some(s => s.code === code)
}

async function addToPortfolio(stock) {
  if (isBookmarked(stock.code)) return

  try {
    // POST /portfolio  →  { user_id, stock_code, stock_name }
    await axios.post(`${BASE_URL}/portfolio`, {
      user_id: userId.value,
      stock_code: stock.code,
      stock_name: stock.name
    })
    portfolio.value.push({ ...stock })
    loadAllPrices()
    showMessage(`${stock.name}을(를) 포트폴리오에 추가했습니다`, 'success')
    searchQuery.value = ''
    searchResults.value = []
  } catch (error) {
    showMessage(error.response?.data?.message || '추가에 실패했습니다', 'error')
  }
}

async function removeFromPortfolio(code) {
  const stock = portfolio.value.find(s => s.code === code)
  try {
    // DELETE /portfolio  →  { user_id, stock_code }
    await axios.delete(`${BASE_URL}/portfolio`, {
      data: { user_id: userId.value, stock_code: code }
    })
    portfolio.value = portfolio.value.filter(s => s.code !== code)
    showMessage(`${stock.name}을(를) 포트폴리오에서 제거했습니다`, 'success')
  } catch (error) {
    showMessage(error.response?.data?.message || '제거에 실패했습니다', 'error')
  }
}

function showMessage(msg, type) {
  apiMessage.value = msg
  apiMessageType.value = type
  setTimeout(() => { apiMessage.value = '' }, 3000)
}

// ── 티커/차트 더미 데이터 ──
const tickerItems = ref([
  { name: 'KOSPI', value: '2,623.45', change: 0.87 },
  { name: 'KOSDAQ', value: '748.32', change: -0.43 },
  { name: 'NASDAQ', value: '19,245.30', change: 1.24 },
  { name: 'S&P500', value: '5,308.12', change: 0.62 },
  { name: 'DOW', value: '39,872.00', change: -0.18 },
  { name: '닛케이', value: '38,450.20', change: 0.55 },
  { name: 'WTI', value: '78.40달러', change: -0.32 },
  { name: '금', value: '2,345달러', change: 0.21 },
  { name: '환율(USD)', value: '1,342원', change: -0.15 },
])

const recommendedStocks = ref([
  { rank: 1, name: '삼성전자', code: '005930', price: '71,500원', change: 2.3, reason: '반도체 수출 증가', sparkline: '0,20 10,18 20,22 30,15 40,12 50,10 60,6' },
  { rank: 2, name: 'SK하이닉스', code: '000660', price: '138,000원', change: 1.8, reason: 'HBM 수요 급증', sparkline: '0,22 10,20 20,18 30,16 40,14 50,10 60,8' },
  { rank: 3, name: 'NAVER', code: '035420', price: '182,500원', change: -0.5, reason: 'AI 서비스 확장', sparkline: '0,8 10,10 20,12 30,14 40,16 50,18 60,20' },
  { rank: 4, name: '카카오', code: '035720', price: '42,300원', change: 0.9, reason: '핀테크 성장세', sparkline: '0,18 10,16 20,20 30,14 40,12 50,10 60,8' },
  { rank: 5, name: 'LG에너지솔루션', code: '373220', price: '312,000원', change: -1.2, reason: '배터리 수주 소식', sparkline: '0,6 10,10 20,12 30,14 40,18 50,20 60,22' },
])

const kospiNews = ref([
  { id: 1, title: '외국인 순매수 4거래일 연속' },
  { id: 2, title: '삼성전자 52주 신고가 경신' },
  { id: 3, title: '코스피 2,650 돌파 시도' },
])
const kosdaqNews = ref([
  { id: 1, title: '이차전지·바이오 테마 강세' },
  { id: 2, title: '코스닥 외국인 순매수 지속' },
  { id: 3, title: '중소형 성장주 관심 확대' },
])

// 지수 실시간 데이터
const kospiData = ref(null)
const kosdaqData = ref(null)

function formatIndexDisplay(data) {
  if (!data || !data.value) return { value: '-', drate: '-', isUp: true }
  const sign = data.sign || '3'
  const isUp = sign === '1' || sign === '2'
  const drateNum = parseFloat(data.drate || '0')
  const valueNum = parseFloat(data.value)
  const valueStr = isNaN(valueNum)
    ? data.value
    : valueNum.toLocaleString('ko-KR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return {
    value: valueStr,
    drate: `${isUp ? '▲' : '▼'} ${Math.abs(drateNum).toFixed(2)}%`,
    isUp,
  }
}

const kospiDisplay = computed(() => formatIndexDisplay(kospiData.value))
const kosdaqDisplay = computed(() => formatIndexDisplay(kosdaqData.value))

function formatGlobalPrice(name, price) {
  if (name === 'WTI' || name === '금') return price.toLocaleString('en-US', { maximumFractionDigits: 2 }) + '달러'
  if (name === '환율(USD)') return Math.round(price).toLocaleString('ko-KR') + '원'
  return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadGlobalIndices() {
  try {
    const res = await axios.get(`${BASE_URL}/market/global`)
    const data = res.data

    tickerItems.value = tickerItems.value.map(item => {
      const d = data[item.name]
      if (!d) return item
      if (item.name === 'KOSPI' && kospiData.value?.value) return item
      if (item.name === 'KOSDAQ' && kosdaqData.value?.value) return item
      return { ...item, value: formatGlobalPrice(item.name, d.price), change: d.change }
    })

    // 마켓 카드: LS 실시간 없을 때 yfinance 종가로 표시
    if (!kospiData.value?.value && data['KOSPI']) {
      const d = data['KOSPI']
      kospiData.value = { value: String(d.price), drate: String(Math.abs(d.change)), sign: d.change >= 0 ? '2' : '5', change: String(Math.abs(d.change)) }
    }
    if (!kosdaqData.value?.value && data['KOSDAQ']) {
      const d = data['KOSDAQ']
      kosdaqData.value = { value: String(d.price), drate: String(Math.abs(d.change)), sign: d.change >= 0 ? '2' : '5', change: String(Math.abs(d.change)) }
    }
  } catch (_) {}
}

async function loadMarketIndices() {
  try {
    const res = await axios.get(`${BASE_URL}/market/indices`)
    const data = res.data
    if (data.kospi?.value) {
      kospiData.value = data.kospi
      const d = formatIndexDisplay(data.kospi)
      const isUp = data.kospi.sign === '1' || data.kospi.sign === '2'
      const drate = parseFloat(data.kospi.drate || '0')
      tickerItems.value = tickerItems.value.map((item, i) =>
        i === 0 ? { name: 'KOSPI', value: d.value, change: isUp ? drate : -drate } : item
      )
    }
    if (data.kosdaq?.value) {
      kosdaqData.value = data.kosdaq
      const d = formatIndexDisplay(data.kosdaq)
      const isUp = data.kosdaq.sign === '1' || data.kosdaq.sign === '2'
      const drate = parseFloat(data.kosdaq.drate || '0')
      tickerItems.value = tickerItems.value.map((item, i) =>
        i === 1 ? { name: 'KOSDAQ', value: d.value, change: isUp ? drate : -drate } : item
      )
    }
  } catch (_) {}
}
const newsList = ref([])

function handleLogout() {
  localStorage.removeItem('user_id')
  localStorage.removeItem('username')
  router.push('/')
}

async function loadPortfolio() {
  if (!userId.value) return
  try {
    const res = await axios.get(`${BASE_URL}/portfolio`, { params: { user_id: userId.value } })
    portfolio.value = (res.data.items || []).map(item => ({
      name: item.stock_name,
      code: item.stock_code,
      price: '-',
      change: 0,
    }))
  } catch (_) {}
}

async function loadRecommendations() {
  try {
    const res = await axios.get(`${BASE_URL}/recommendations/latest`)
    const data = res.data
    if (data && Array.isArray(data.recommendations) && data.recommendations.length > 0) {
      const updatedAt = timeAgo(data.analyzed_at)
      recommendedStocks.value = data.recommendations.map(r => ({
        rank: r.rank,
        name: r.stock_name,
        code: r.stock_code || String(r.rank),
        price: '-',
        change: 0,
        reason: r.reason || r.news_evidence || '',
        sparkline: '0,20 10,18 20,22 30,15 40,12 50,10 60,6',
      }))
      topThemesCount.value = Array.isArray(data.top_themes) ? data.top_themes.length : '-'
      analysisUpdatedAt.value = updatedAt

      // 마켓 카드 뉴스 업데이트
      const mn = data.market_news
      if (mn?.kospi?.length > 0)
        kospiNews.value = mn.kospi.map((t, i) => ({ id: i + 1, title: t }))
      if (mn?.kosdaq?.length > 0)
        kosdaqNews.value = mn.kosdaq.map((t, i) => ({ id: i + 1, title: t }))

      const items = []
      if (data.overall_market_summary) {
        items.push({ id: 0, tag: '시장요약', title: data.overall_market_summary, time: updatedAt })
      }
      data.recommendations.forEach(r => {
        if (r.news_evidence) {
          items.push({ id: r.rank, tag: r.theme || '분석', title: r.news_evidence, time: updatedAt })
        }
      })
      if (items.length > 0) newsList.value = items
    }
  } catch (_) {}
}

function calcSparkline(prices) {
  if (!prices || prices.length < 2) return '0,14 60,14'
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const pad = 2
  return prices.map((p, i) => {
    const x = (i / (prices.length - 1)) * 60
    const y = pad + (1 - (p - min) / range) * (28 - pad * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

async function loadAllPrices() {
  const recCodes = recommendedStocks.value.filter(s => s.code && !s.code.startsWith('TBD_')).map(s => s.code)
  const portCodes = portfolio.value.filter(s => s.code && !s.code.startsWith('TBD_')).map(s => s.code)
  const allCodes = [...new Set([...recCodes, ...portCodes])]
  if (!allCodes.length) return
  try {
    const res = await axios.get(`${BASE_URL}/stocks/price`, { params: { codes: allCodes.join(',') } })
    const priceData = res.data

    recommendedStocks.value = recommendedStocks.value.map(stock => {
      const prices = priceData[stock.code]
      if (!prices || prices.length < 2) return stock
      const last = prices[prices.length - 1]
      const prev = prices[prices.length - 2]
      const change = parseFloat(((last - prev) / prev * 100).toFixed(2))
      return { ...stock, price: last.toLocaleString('ko-KR') + '원', change, sparkline: calcSparkline(prices) }
    })

    portfolio.value = portfolio.value.map(stock => {
      const prices = priceData[stock.code]
      if (!prices || prices.length < 2) return stock
      const last = prices[prices.length - 1]
      const prev = prices[prices.length - 2]
      const change = parseFloat(((last - prev) / prev * 100).toFixed(2))
      return { ...stock, price: last.toLocaleString('ko-KR') + '원', change }
    })
  } catch (_) {}
}

let refreshTimer = null
let indicesTimer = null

onMounted(async () => {
  await loadRecommendations()
  await loadMarketIndices()
  await loadPortfolio()
  loadAllPrices()
  loadGlobalIndices()
  refreshTimer = setInterval(loadRecommendations, 60 * 1000)
  indicesTimer = setInterval(loadMarketIndices, 30 * 1000)
  setInterval(loadGlobalIndices, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (indicesTimer) clearInterval(indicesTimer)
})
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }
.main-wrapper {
  display: flex; flex-direction: column; min-height: 100vh;
  background: #f1f5f9;
  font-family: 'Pretendard', 'Noto Sans KR', sans-serif; color: #1e293b;
}

/* 티커 */
.ticker-bar {
  width: 100%; background: #1e293b; color: #fff;
  height: 40px; overflow: hidden; display: flex;
  align-items: center; position: sticky; top: 0; z-index: 100;
}
.ticker-track { overflow: hidden; width: 100%; }
.ticker-inner { display: flex; width: max-content; animation: ticker-scroll 35s linear infinite; }
@keyframes ticker-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
.ticker-item { display: flex; align-items: center; gap: 6px; padding: 0 20px; white-space: nowrap; font-size: 13px; }
.ticker-name { color: #94a3b8; font-weight: 500; }
.ticker-value { font-weight: 600; }
.ticker-change { font-size: 12px; font-weight: 600; }
.ticker-change.up { color: #f87171; }
.ticker-change.down { color: #60a5fa; }
.ticker-divider { color: #334155; }

.body-wrapper { display: flex; flex: 1; position: relative; }

.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 150; }

.menu-btn {
  position: fixed; top: 52px; left: 16px; z-index: 200;
  width: 40px; height: 40px; border: none; background: #fff;
  border-radius: 10px; cursor: pointer; display: flex;
  align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.hamburger { display: flex; flex-direction: column; gap: 4px; }
.hamburger span { display: block; width: 18px; height: 2px; background: #1e293b; border-radius: 2px; transition: all 0.3s; }
.hamburger.open span:nth-child(1) { transform: rotate(45deg) translate(4px, 4px); }
.hamburger.open span:nth-child(2) { opacity: 0; }
.hamburger.open span:nth-child(3) { transform: rotate(-45deg) translate(4px, -4px); }

.sidebar {
  position: fixed; top: 40px; left: 0; height: calc(100vh - 40px);
  width: 260px; background: #fff; border-right: 1px solid #e2e8f0;
  display: flex; flex-direction: column; padding: 20px 16px;
  z-index: 160; transform: translateX(-100%);
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 4px 0 16px rgba(0,0,0,0.08);
}
.sidebar.open { transform: translateX(0); }
.sidebar-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.sidebar-logo { display: flex; align-items: center; gap: 8px; }
.logo-icon { font-size: 22px; }
.logo-text { font-size: 18px; font-weight: 700; }
.sidebar-close { border: none; background: transparent; font-size: 16px; color: #94a3b8; cursor: pointer; padding: 4px 8px; border-radius: 6px; }
.sidebar-close:hover { background: #f1f5f9; }
.sidebar-user { display: flex; align-items: center; gap: 10px; padding: 14px; background: #f8fafc; border-radius: 12px; margin-bottom: 20px; }
.user-avatar { width: 38px; height: 38px; border-radius: 50%; background: #2563eb; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; flex-shrink: 0; }
.user-name { font-size: 14px; font-weight: 600; }
.user-role { font-size: 12px; color: #94a3b8; }
.nav-section-label { font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.08em; text-transform: uppercase; padding: 0 12px; margin-bottom: 6px; }
.sidebar-nav { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 11px 14px; border: none; background: transparent; color: #64748b; border-radius: 10px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; text-align: left; width: 100%; }
.nav-item:hover { background: #f1f5f9; color: #1e293b; }
.nav-item.active { background: #eff6ff; color: #2563eb; font-weight: 700; }
.nav-badge { margin-left: auto; background: #2563eb; color: #fff; font-size: 11px; font-weight: 700; padding: 1px 7px; border-radius: 20px; }
.logout-btn { width: 100%; padding: 10px; border: 1px solid #e2e8f0; background: transparent; color: #94a3b8; border-radius: 8px; font-size: 13px; cursor: pointer; margin-top: 16px; }
.logout-btn:hover { background: #f1f5f9; color: #1e293b; }

/* 메인 */
.content { flex: 1; padding: 32px 32px 32px 72px; width: 100%; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
.page-sub { font-size: 13px; color: #94a3b8; }

.two-col { display: grid; grid-template-columns: 1fr 300px; gap: 20px; align-items: start; }
.summary-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.summary-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
.card-label { font-size: 12px; color: #94a3b8; margin-bottom: 6px; }
.card-value { font-size: 22px; font-weight: 700; }
.card-unit { font-size: 12px; color: #94a3b8; }
.updated { font-size: 14px; color: #16a34a; }
.section-title { font-size: 14px; font-weight: 700; color: #475569; margin-bottom: 10px; }

.stock-list { display: flex; flex-direction: column; gap: 8px; }
.stock-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 16px; display: flex; align-items: center; gap: 12px; transition: border 0.2s, box-shadow 0.2s; }
.stock-card:hover { border-color: #93c5fd; box-shadow: 0 4px 12px rgba(37,99,235,0.08); }
.stock-rank { width: 26px; height: 26px; border-radius: 50%; background: #eff6ff; color: #2563eb; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; flex-shrink: 0; }
.stock-info { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.stock-name { font-size: 13px; font-weight: 600; }
.stock-code { font-size: 11px; color: #94a3b8; }
.stock-sparkline { flex-shrink: 0; }
.stock-right { text-align: right; flex-shrink: 0; min-width: 80px; }
.stock-price { font-size: 13px; font-weight: 600; }
.stock-change { font-size: 12px; font-weight: 600; }
.stock-change.up { color: #ef4444; }
.stock-change.down { color: #2563eb; }
.bookmark-btn { border: none; background: transparent; font-size: 20px; cursor: pointer; color: #cbd5e1; transition: all 0.2s; padding: 2px 4px; border-radius: 6px; flex-shrink: 0; }
.bookmark-btn:hover { color: #f59e0b; }
.bookmark-btn.bookmarked { color: #f59e0b; }

/* 오른쪽 증시 */
.col-right { display: flex; flex-direction: column; gap: 16px; }
.market-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; }
.market-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.market-badge { display: inline-block; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; margin-bottom: 6px; }
.market-badge.kospi { background: #fef2f2; color: #ef4444; }
.market-badge.nasdaq { background: #eff6ff; color: #2563eb; }
.market-badge.kosdaq { background: #f0fdf4; color: #16a34a; }
.market-value { font-size: 20px; font-weight: 700; }
.market-change { font-size: 13px; font-weight: 600; }
.market-change.up { color: #ef4444; }
.news-section-label { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.market-news-list { display: flex; flex-direction: column; gap: 7px; }
.market-news-item { display: flex; align-items: flex-start; gap: 8px; font-size: 12px; color: #475569; line-height: 1.5; }
.news-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.news-dot.red { background: #ef4444; }
.news-dot.blue { background: #2563eb; }
.news-dot.green { background: #16a34a; }

/* 검색창 */
.search-box { position: relative; margin-bottom: 20px; }
.search-input {
  width: 100%; padding: 14px 48px 14px 20px;
  background: #fff; border: 2px solid #e2e8f0;
  border-radius: 14px; font-size: 14px; color: #1e293b;
  outline: none; transition: border 0.2s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.search-input:focus { border-color: #2563eb; }
.search-input::placeholder { color: #94a3b8; }
.search-icon { position: absolute; right: 16px; top: 50%; transform: translateY(-50%); font-size: 18px; pointer-events: none; }

.search-dropdown {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1); z-index: 50; overflow: hidden;
}
.search-result-item {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 20px; cursor: pointer; transition: background 0.15s;
  border-bottom: 1px solid #f1f5f9;
}
.search-result-item:last-child { border-bottom: none; }
.search-result-item:hover { background: #f8fafc; }
.result-name { font-size: 14px; font-weight: 600; margin-bottom: 2px; }
.result-code { font-size: 12px; color: #94a3b8; }
.result-right { margin-left: auto; text-align: right; }
.result-price { font-size: 13px; font-weight: 600; margin-bottom: 2px; }
.result-change { font-size: 12px; font-weight: 600; }
.result-change.up { color: #ef4444; }
.result-change.down { color: #2563eb; }
.add-btn {
  padding: 6px 14px; border-radius: 8px; border: 1px solid #2563eb;
  background: transparent; color: #2563eb; font-size: 12px; font-weight: 600;
  cursor: pointer; white-space: nowrap; transition: all 0.2s; flex-shrink: 0;
}
.add-btn:hover { background: #2563eb; color: #fff; }
.add-btn.added { background: #f0fdf4; border-color: #16a34a; color: #16a34a; cursor: default; }
.no-result { padding: 20px; text-align: center; color: #94a3b8; font-size: 14px; }

/* API 알림 */
.api-message {
  padding: 12px 20px; border-radius: 10px; font-size: 13px;
  font-weight: 500; margin-bottom: 16px;
}
.api-message.success { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.api-message.error { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca; }

/* 포트폴리오 목록 */
.portfolio-list { display: flex; flex-direction: column; gap: 10px; }
.portfolio-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 16px 20px; display: flex; align-items: center; gap: 16px;
  transition: border 0.2s, box-shadow 0.2s;
}
.portfolio-card:hover { border-color: #93c5fd; box-shadow: 0 4px 12px rgba(37,99,235,0.08); }
.portfolio-info { display: flex; align-items: center; gap: 12px; flex: 1; }
.portfolio-price { text-align: right; min-width: 90px; }
.remove-btn {
  padding: 6px 14px; border-radius: 8px; border: 1px solid #fecaca;
  background: #fef2f2; color: #ef4444; font-size: 12px; font-weight: 600;
  cursor: pointer; white-space: nowrap; transition: all 0.2s; flex-shrink: 0;
}
.remove-btn:hover { background: #ef4444; color: #fff; }

/* 뉴스 탭 */
.news-list { display: flex; flex-direction: column; gap: 12px; }
.news-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px 24px; cursor: pointer; transition: border 0.2s; }
.news-card:hover { border-color: #93c5fd; }
.news-tag { display: inline-block; background: #eff6ff; color: #2563eb; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; margin-bottom: 10px; }
.news-title { font-size: 15px; font-weight: 500; margin-bottom: 8px; }
.news-time { font-size: 12px; color: #94a3b8; }

.empty-state { text-align: center; padding: 80px; color: #94a3b8; font-size: 15px; line-height: 2; }
.empty-state p:first-child { font-size: 48px; }
.empty-sub { font-size: 13px; }
</style>
