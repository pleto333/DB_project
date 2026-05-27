<template>
  <div class="detail-wrapper">

    <!-- 상단 헤더 -->
    <header class="detail-header">
      <button class="back-btn" @click="goBack">← 뒤로</button>
      <div class="header-stock-info">
        <span class="header-name">{{ stock.name }}</span>
        <span class="header-code">{{ stock.code }}</span>
      </div>
    </header>

    <div class="detail-content">

      <!-- 주식 기본 정보 -->
      <div class="stock-hero">
        <div class="stock-hero-left">
          <h1 class="hero-name">{{ stock.name }}</h1>
          <p class="hero-code">{{ stock.code }} · 코스피</p>
          <p class="hero-price">{{ stock.price }}</p>
          <p :class="['hero-change', stock.change > 0 ? 'up' : 'down']">
            {{ stock.change > 0 ? '▲' : '▼' }} {{ Math.abs(stock.change) }}%
            <span class="change-label">오늘</span>
          </p>
        </div>
        <div class="stock-hero-right">
          <!-- 스파크라인 -->
          <svg width="160" height="60" viewBox="0 0 160 60">
            <defs>
              <linearGradient :id="'heroGrad'" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="stock.change > 0 ? '#ef4444' : '#2563eb'" stop-opacity="0.2"/>
                <stop offset="100%" :stop-color="stock.change > 0 ? '#ef4444' : '#2563eb'" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <polygon :points="stock.areaLine" :fill="'url(#heroGrad)'"/>
            <polyline :points="stock.chartLine"
              fill="none"
              :stroke="stock.change > 0 ? '#ef4444' : '#2563eb'"
              stroke-width="2" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>

      <!-- LLM 분석 결과 -->
      <div :class="['analysis-card', stock.recommend ? 'recommend' : 'not-recommend']">
        <div class="analysis-header">
          <div class="analysis-badge">
            <span class="badge-icon">{{ stock.recommend ? '🤖' : '🤖' }}</span>
            <span>AI 분석 결과</span>
          </div>
          <div :class="['verdict-badge', stock.recommend ? 'buy' : 'sell']">
            {{ stock.recommend ? '✓ 매수 추천' : '✕ 매수 비추천' }}
          </div>
        </div>

        <!-- 신뢰도 게이지 -->
        <div class="confidence-section">
          <div class="confidence-label">
            <span>AI 신뢰도</span>
            <span class="confidence-value">{{ stock.confidence }}%</span>
          </div>
          <div class="confidence-bar">
            <div class="confidence-fill"
              :style="{ width: stock.confidence + '%', background: stock.recommend ? '#ef4444' : '#2563eb' }">
            </div>
          </div>
        </div>

        <!-- 한줄 요약 -->
        <p class="analysis-summary">{{ stock.summary }}</p>
      </div>

      <!-- 2컬럼 -->
      <div class="two-col">

        <!-- 왼쪽: 분석 근거 -->
        <div class="col-left">

          <!-- 긍정 요인 -->
          <div class="factor-card positive" v-if="stock.positives.length > 0">
            <p class="factor-title">📈 긍정 요인</p>
            <div class="factor-item" v-for="(item, i) in stock.positives" :key="i">
              <span class="factor-dot green"></span>
              <span>{{ item }}</span>
            </div>
          </div>

          <!-- 부정 요인 -->
          <div class="factor-card negative" v-if="stock.negatives.length > 0">
            <p class="factor-title">📉 부정 요인</p>
            <div class="factor-item" v-for="(item, i) in stock.negatives" :key="i">
              <span class="factor-dot red"></span>
              <span>{{ item }}</span>
            </div>
          </div>

          <!-- 상세 분석 -->
          <div class="detail-analysis-card">
            <p class="factor-title">🧠 LLM 상세 분석</p>
            <p class="detail-analysis-text">{{ stock.detailAnalysis }}</p>
          </div>

        </div>

        <!-- 오른쪽: 관련 뉴스 -->
        <div class="col-right">
          <p class="section-title">📰 분석 근거 뉴스</p>
          <div class="related-news-list">
            <div class="related-news-item" v-for="news in stock.relatedNews" :key="news.id">
              <div class="news-top">
                <span :class="['news-sentiment', news.sentiment]">
                  {{ news.sentiment === 'positive' ? '긍정' : news.sentiment === 'negative' ? '부정' : '중립' }}
                </span>
                <span class="news-time">{{ news.time }}</span>
              </div>
              <p class="news-title">{{ news.title }}</p>
              <p class="news-desc">{{ news.desc }}</p>
            </div>
          </div>

          <!-- 포트폴리오 추가 버튼 -->
          <button class="portfolio-btn" @click="togglePortfolio"
            :class="{ added: isAdded }">
            {{ isAdded ? '★ 포트폴리오에서 제거' : '☆ 포트폴리오에 추가' }}
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const BASE_URL = 'http://localhost:8080'

const isAdded = ref(false)
const userId = ref(localStorage.getItem('user_id') || '')

// TODO: 실제로는 route.params.code 로 백엔드에서 받아오기
// GET /stocks/:code/analysis
const stock = ref({
  name: '삼성전자',
  code: route.params.code || '005930',
  price: '71,500원',
  change: 2.3,
  recommend: true,
  confidence: 82,
  summary: '반도체 수출 증가와 HBM 수요 급증으로 단기 상승 모멘텀이 강하게 형성되어 있습니다. AI 서버 투자 확대에 따른 수혜가 예상됩니다.',
  positives: [
    '2분기 반도체 수출액 전년 대비 34% 증가',
    'HBM3E 엔비디아 공급 계약 체결 보도',
    '외국인 투자자 4거래일 연속 순매수',
    '증권사 목표주가 상향 조정 잇따라',
  ],
  negatives: [
    '중국 반도체 자급률 상승으로 장기 수요 불확실',
    '원달러 환율 하락 시 수출 수익성 감소 우려',
  ],
  detailAnalysis: '최근 5일간 LS증권 뉴스 128건을 분석한 결과, 삼성전자 관련 긍정 뉴스 비율이 74%로 높게 나타났습니다. 특히 HBM 관련 뉴스에서 긍정 감성 지수가 0.87로 매우 높았으며, 외국인 매수세 유입과 함께 기술적 지지선인 70,000원을 안정적으로 유지하고 있습니다. 단기(1~2주) 관점에서 매수 추천이며, 75,000원을 1차 목표가로 제시합니다.',
  chartLine: '0,50 20,45 40,48 60,35 80,30 100,25 120,20 140,15 160,10',
  areaLine: '0,50 20,45 40,48 60,35 80,30 100,25 120,20 140,15 160,10 160,60 0,60',
  relatedNews: [
    { id: 1, sentiment: 'positive', time: '5분 전', title: '삼성전자, HBM3E 엔비디아 공급 계약 체결', desc: '삼성전자가 엔비디아와 HBM3E 메모리 공급 계약을 체결했다고 업계 관계자가 밝혔다.' },
    { id: 2, sentiment: 'positive', time: '1시간 전', title: '반도체 수출 34% 증가... 삼성·SK 수혜 집중', desc: '산업통상자원부에 따르면 2분기 반도체 수출이 전년 동기 대비 34% 증가한 것으로 나타났다.' },
    { id: 3, sentiment: 'neutral', time: '3시간 전', title: '삼성전자 목표주가 80,000원으로 상향 - 미래에셋', desc: '미래에셋증권은 삼성전자 목표주가를 기존 75,000원에서 80,000원으로 상향 조정했다.' },
    { id: 4, sentiment: 'negative', time: '5시간 전', title: '중국 반도체 자급률 2030년 70% 목표 발표', desc: '중국 정부가 2030년까지 반도체 자급률 70% 달성을 목표로 추가 지원책을 발표했다.' },
  ]
})

onMounted(async () => {
  try {
    const res = await axios.get(`${BASE_URL}/recommendations/latest`)
    const data = res.data
    if (!data || !data.recommendations) return

    const rec = data.recommendations.find(r =>
      r.stock_code === route.params.code || String(r.rank) === route.params.code
    )
    if (!rec) return

    const confidenceMap = { '상': 85, '중': 60, '하': 35 }
    stock.value = {
      name: rec.stock_name,
      code: rec.stock_code,
      price: '-',
      change: 0,
      recommend: rec.confidence !== '하',
      confidence: confidenceMap[rec.confidence] ?? 60,
      summary: rec.reason,
      positives: [rec.expected_momentum].filter(Boolean),
      negatives: [rec.risk].filter(Boolean),
      detailAnalysis: rec.reason + (rec.news_evidence ? '\n\n[분석 근거] ' + rec.news_evidence : ''),
      chartLine: '0,50 20,45 40,48 60,35 80,30 100,25 120,20 140,15 160,10',
      areaLine: '0,50 20,45 40,48 60,35 80,30 100,25 120,20 140,15 160,10 160,60 0,60',
      relatedNews: rec.news_evidence ? [{
        id: 1,
        sentiment: rec.confidence === '하' ? 'negative' : 'positive',
        time: data.analysis_date || '-',
        title: `[${rec.theme}] ${rec.stock_name} 분석 근거`,
        desc: rec.news_evidence,
      }] : [],
    }
  } catch (_) {
    // DB 미연결 시 더미 데이터 유지
  }

  // 현재 포트폴리오에 이미 추가되어 있는지 확인
  if (userId.value && stock.value.code) {
    try {
      const res = await axios.get(`${BASE_URL}/portfolio`, { params: { user_id: userId.value } })
      const items = res.data.items || []
      isAdded.value = items.some(item => item.code === stock.value.code)
    } catch (_) {}
  }
})

async function togglePortfolio() {
  if (!userId.value) {
    alert('로그인이 필요합니다.')
    return
  }
  try {
    if (isAdded.value) {
      await axios.delete(`${BASE_URL}/portfolio`, {
        data: { user_id: userId.value, stock_code: stock.value.code }
      })
      isAdded.value = false
    } else {
      await axios.post(`${BASE_URL}/portfolio`, {
        user_id: userId.value,
        stock_code: stock.value.code,
        stock_name: stock.value.name
      })
      isAdded.value = true
    }
  } catch (err) {
    const msg = err?.response?.data?.detail?.message || err?.response?.data?.detail || '포트폴리오 처리 중 오류가 발생했습니다.'
    alert(msg)
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.detail-wrapper {
  min-height: 100vh; background: #f1f5f9;
  font-family: 'Pretendard', 'Noto Sans KR', sans-serif; color: #1e293b;
}

/* 헤더 */
.detail-header {
  position: sticky; top: 0; z-index: 50;
  background: #fff; border-bottom: 1px solid #e2e8f0;
  padding: 14px 32px; display: flex; align-items: center; gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.back-btn {
  border: none; background: transparent; color: #2563eb;
  font-size: 14px; font-weight: 600; cursor: pointer; padding: 6px 12px;
  border-radius: 8px; transition: background 0.2s;
}
.back-btn:hover { background: #eff6ff; }
.header-stock-info { display: flex; align-items: center; gap: 10px; }
.header-name { font-size: 16px; font-weight: 700; }
.header-code { font-size: 13px; color: #94a3b8; }

.detail-content { padding: 32px; max-width: 1100px; margin: 0 auto; }

/* 히어로 */
.stock-hero {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 20px;
  padding: 28px 32px; display: flex; justify-content: space-between;
  align-items: center; margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.hero-name { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
.hero-code { font-size: 13px; color: #94a3b8; margin-bottom: 12px; }
.hero-price { font-size: 32px; font-weight: 700; margin-bottom: 6px; }
.hero-change { font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.hero-change.up { color: #ef4444; }
.hero-change.down { color: #2563eb; }
.change-label { font-size: 13px; color: #94a3b8; font-weight: 400; }

/* LLM 분석 카드 */
.analysis-card {
  border-radius: 20px; padding: 24px 28px; margin-bottom: 20px;
  border: 2px solid;
}
.analysis-card.recommend { background: #fff9f9; border-color: #fecaca; }
.analysis-card.not-recommend { background: #f0f4ff; border-color: #bfdbfe; }
.analysis-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.analysis-badge { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: #475569; }
.badge-icon { font-size: 20px; }
.verdict-badge {
  padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: 700;
}
.verdict-badge.buy { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca; }
.verdict-badge.sell { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }

.confidence-section { margin-bottom: 16px; }
.confidence-label { display: flex; justify-content: space-between; font-size: 13px; color: #64748b; margin-bottom: 6px; }
.confidence-value { font-weight: 700; color: #1e293b; }
.confidence-bar { height: 8px; background: #e2e8f0; border-radius: 20px; overflow: hidden; }
.confidence-fill { height: 100%; border-radius: 20px; transition: width 0.8s ease; }

.analysis-summary { font-size: 15px; color: #334155; line-height: 1.7; font-weight: 500; }

/* 2컬럼 */
.two-col { display: grid; grid-template-columns: 1fr 360px; gap: 20px; align-items: start; }

/* 요인 카드 */
.factor-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
  padding: 20px 24px; margin-bottom: 16px;
}
.factor-card.positive { border-left: 4px solid #ef4444; }
.factor-card.negative { border-left: 4px solid #2563eb; }
.factor-title { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 14px; }
.factor-item { display: flex; align-items: flex-start; gap: 10px; font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 8px; }
.factor-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; margin-top: 7px; }
.factor-dot.green { background: #ef4444; }
.factor-dot.red { background: #2563eb; }

.detail-analysis-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px 24px;
}
.detail-analysis-text { font-size: 14px; color: #475569; line-height: 1.8; }

/* 오른쪽 */
.section-title { font-size: 14px; font-weight: 700; color: #475569; margin-bottom: 12px; }
.related-news-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }
.related-news-item {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px 18px;
}
.news-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.news-sentiment {
  font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 20px;
}
.news-sentiment.positive { background: #fef2f2; color: #ef4444; }
.news-sentiment.negative { background: #eff6ff; color: #2563eb; }
.news-sentiment.neutral { background: #f1f5f9; color: #64748b; }
.news-time { font-size: 12px; color: #94a3b8; }
.news-title { font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 6px; line-height: 1.5; }
.news-desc { font-size: 12px; color: #94a3b8; line-height: 1.5; }

.portfolio-btn {
  width: 100%; padding: 14px; border-radius: 12px; font-size: 14px;
  font-weight: 700; cursor: pointer; transition: all 0.2s;
  border: 2px solid #2563eb; background: transparent; color: #2563eb;
}
.portfolio-btn:hover { background: #2563eb; color: #fff; }
.portfolio-btn.added { background: #f0fdf4; border-color: #16a34a; color: #16a34a; }
.portfolio-btn.added:hover { background: #16a34a; color: #fff; }
</style>
