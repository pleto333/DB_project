<script setup>
import { computed, onMounted, ref } from "vue";

const loading = ref(true);
const errorMessage = ref("");
const analyses = ref([]);
const recommendations = ref([]);
const newsArticles = ref([]);
const analysisId = ref("all");
const dataSource = ref("-");
const selectedRecommendation = ref(null);
const recommendationFilter = ref("ALL");
const marketTickerItems = [
  { label: "KOSPI", value: "2,687.45", change: "+0.00", rate: "+0.00%" },
  { label: "KOSDAQ", value: "842.31", change: "+0.00", rate: "+0.00%" },
  { label: "USD/KRW", value: "1,378.50", change: "+0.00", rate: "+0.00%" },
  { label: "VKOSPI", value: "17.82", change: "+1.45", rate: "+8.85%" },
  { label: "개인", value: "+0억", change: "순매수", rate: "" },
  { label: "외국인", value: "-0억", change: "순매도", rate: "" },
  { label: "기관", value: "+0억", change: "순매수", rate: "" },
];
const exchangeRate = {
  symbol: "USDKRW",
  name: "미국 달러 / 대한민국 원",
  value: "1,378.50",
  change: "+0.00",
  rate: "+0.00%",
};
const fearIndex = {
  label: "코스피 공포 지수",
  value: 42,
  status: "중립",
};
const kospiChart = {
  label: "코스피 차트",
  value: "2,687.45",
  change: "+0.00",
  rate: "+0.00%",
  points: [2580, 2598, 2606, 2628, 2620, 2634, 2648, 2660, 2652, 2674, 2692, 2687],
};
const sectorDashboard = {
  date: "2026년 5월 22일 금요일",
  updatedAt: "오후 04:19:23",
  kospi: { value: "2,687.45", change: "+0.41%", point: "+32.12" },
  kosdaq: { value: "842.31", change: "+1.29%", point: "+10.72" },
  strong: [
    { name: "전기장비와기기", rate: "+8.12%" },
    { name: "석유와가스", rate: "+7.37%" },
    { name: "건강관리기술", rate: "+7.35%" },
    { name: "생명과학도구및서비스", rate: "+6.82%" },
    { name: "생물공학", rate: "+6.58%" },
  ],
  weak: [
    { name: "백화점과일반상점", rate: "-2.75%" },
    { name: "기타금융", rate: "-2.20%" },
    { name: "다각화된소비자서비스", rate: "-1.87%" },
    { name: "자동차", rate: "-1.62%" },
    { name: "반도체와반도체장비", rate: "-0.97%" },
  ],
};
const demoAnalyses = [
  {
    analysis_id: 1,
    model_name: "gpt-example",
    input_summary: "AI 반도체 수요, HBM 공급 부족, 반도체 수출 회복 뉴스는 반도체 대형주에 긍정적이다.",
    theme: "반도체",
    analyzed_at: "2026-05-09 10:00:00",
    recommendation_count: 2,
    news_count: 3,
  },
  {
    analysis_id: 2,
    model_name: "gpt-example",
    input_summary: "전기차 판매 회복, 배터리 소재 가격 안정, 북미 공장 투자 확대 뉴스는 배터리 업종에 긍정적이다.",
    theme: "2차전지",
    analyzed_at: "2026-05-12 11:00:00",
    recommendation_count: 3,
    news_count: 3,
  },
  {
    analysis_id: 3,
    model_name: "gpt-example",
    input_summary: "광고 시장 둔화와 커머스 경쟁 심화 뉴스는 플랫폼 업종에 단기 부담으로 작용할 수 있다.",
    theme: "플랫폼",
    analyzed_at: "2026-05-11 12:00:00",
    recommendation_count: 2,
    news_count: 2,
  },
];
const demoRecommendations = [
  {
    analysis_id: 1,
    theme: "반도체",
    rank_no: 1,
    stock_code: "005930",
    stock_name: "삼성전자",
    recommendation: "BUY",
    reason: "AI 서버 투자 확대로 메모리와 반도체 수요 증가가 기대된다.",
    confidence: 0.87,
  },
  {
    analysis_id: 1,
    theme: "반도체",
    rank_no: 2,
    stock_code: "000660",
    stock_name: "SK하이닉스",
    recommendation: "BUY",
    reason: "HBM 수요 확대와 메모리 업황 회복 기대가 크다.",
    confidence: 0.84,
  },
  {
    analysis_id: 2,
    theme: "2차전지",
    rank_no: 1,
    stock_code: "373220",
    stock_name: "LG에너지솔루션",
    recommendation: "BUY",
    reason: "전기차 수요 회복과 북미 생산 확대에 따른 성장 기대가 있다.",
    confidence: 0.86,
  },
  {
    analysis_id: 2,
    theme: "2차전지",
    rank_no: 2,
    stock_code: "006400",
    stock_name: "삼성SDI",
    recommendation: "BUY",
    reason: "고부가 배터리 중심의 수익성 개선 가능성이 있다.",
    confidence: 0.8,
  },
  {
    analysis_id: 2,
    theme: "2차전지",
    rank_no: 3,
    stock_code: "003670",
    stock_name: "포스코퓨처엠",
    recommendation: "WATCH",
    reason: "소재 가격 안정은 긍정적이지만 업황 회복 확인이 더 필요하다.",
    confidence: 0.69,
  },
  {
    analysis_id: 3,
    theme: "플랫폼",
    rank_no: 1,
    stock_code: "035420",
    stock_name: "NAVER",
    recommendation: "WATCH",
    reason: "광고 성장 둔화와 커머스 경쟁 비용 증가를 확인할 필요가 있다.",
    confidence: 0.72,
  },
  {
    analysis_id: 3,
    theme: "플랫폼",
    rank_no: 2,
    stock_code: "035720",
    stock_name: "카카오",
    recommendation: "WATCH",
    reason: "플랫폼 업종 전반의 광고 둔화 우려가 단기 부담이다.",
    confidence: 0.68,
  },
];
const demoNewsArticles = [
  {
    analysis_id: 1,
    theme: "반도체",
    article_id: 1,
    title: "AI 반도체 수요 증가세 지속",
    summary: "AI 서버 투자가 확대되면서 메모리 반도체 수요가 증가할 가능성이 제기되고 있다.",
    url: "https://news.example.com/ai-semiconductor-demand",
    publisher: "예시경제",
    source: "ls_securities",
    published_at: "2026-05-09 09:00:00",
  },
  {
    analysis_id: 1,
    theme: "반도체",
    article_id: 2,
    title: "HBM 공급 부족 우려 확대",
    summary: "고대역폭 메모리 수요가 빠르게 늘면서 주요 반도체 기업의 실적 개선 기대가 커지고 있다.",
    url: "https://news.example.com/hbm-supply-shortage",
    publisher: "예시증권",
    source: "ls_securities",
    published_at: "2026-05-09 09:20:00",
  },
  {
    analysis_id: 1,
    theme: "반도체",
    article_id: 3,
    title: "반도체 수출 회복세 확인",
    summary: "국내 반도체 수출이 회복 흐름을 보이며 업황 개선 기대가 이어지고 있다.",
    url: "https://news.example.com/semiconductor-export-recovery",
    publisher: "마켓데일리",
    source: "ls_securities",
    published_at: "2026-05-09 09:40:00",
  },
  {
    analysis_id: 2,
    theme: "2차전지",
    article_id: 4,
    title: "전기차 판매 회복 기대",
    summary: "하반기 전기차 판매량 회복 전망이 나오면서 배터리 업종 투자 심리가 개선되고 있다.",
    url: "https://news.example.com/ev-sales-recovery",
    publisher: "예시경제",
    source: "ls_securities",
    published_at: "2026-05-10 10:00:00",
  },
  {
    analysis_id: 2,
    theme: "2차전지",
    article_id: 5,
    title: "배터리 소재 가격 안정세",
    summary: "리튬 등 주요 배터리 소재 가격이 안정되면서 배터리 기업의 수익성 개선 기대가 나오고 있다.",
    url: "https://news.example.com/battery-material-price",
    publisher: "예시증권",
    source: "ls_securities",
    published_at: "2026-05-10 10:20:00",
  },
  {
    analysis_id: 2,
    theme: "2차전지",
    article_id: 6,
    title: "북미 배터리 공장 투자 확대",
    summary: "국내 배터리 기업들이 북미 생산 거점을 확대하며 중장기 성장 기반을 강화하고 있다.",
    url: "https://news.example.com/north-america-battery-investment",
    publisher: "마켓데일리",
    source: "ls_securities",
    published_at: "2026-05-10 10:40:00",
  },
  {
    analysis_id: 3,
    theme: "플랫폼",
    article_id: 7,
    title: "인터넷 플랫폼 기업, 광고 시장 둔화 우려",
    summary: "이번 분기 온라인 광고 시장 성장세가 둔화될 수 있다는 전망이 나오고 있다.",
    url: "https://news.example.com/platform-ad-slowdown",
    publisher: "예시경제",
    source: "ls_securities",
    published_at: "2026-05-11 11:00:00",
  },
  {
    analysis_id: 3,
    theme: "플랫폼",
    article_id: 8,
    title: "커머스 경쟁 심화로 플랫폼 비용 부담 증가",
    summary: "플랫폼 기업들의 커머스 경쟁이 심화되면서 마케팅 비용 증가가 실적 부담 요인으로 거론된다.",
    url: "https://news.example.com/platform-commerce-competition",
    publisher: "예시증권",
    source: "ls_securities",
    published_at: "2026-05-11 11:20:00",
  },
];

const selectedAnalysis = computed(() =>
  analyses.value.find((analysis) => analysis.analysis_id === analysisId.value),
);
const filteredRecommendations = computed(() => {
  if (recommendationFilter.value === "ALL") {
    return recommendations.value;
  }
  return recommendations.value.filter((item) => item.recommendation === recommendationFilter.value);
});
const recommendationCount = computed(() => recommendations.value.length);
const newsCount = computed(() => newsArticles.value.length);
const filters = ["ALL", "BUY", "WATCH"];
const chartPoints = computed(() => {
  const values = kospiChart.points;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = 520;
  const height = 190;
  const padding = 10;
  return values
    .map((value, index) => {
      const x = padding + (index / (values.length - 1)) * (width - padding * 2);
      const y = height - padding - ((value - min) / (max - min || 1)) * (height - padding * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
});
const chartAreaPoints = computed(() => `10,190 ${chartPoints.value} 510,190`);
const fearGaugeStyle = computed(() => ({
  background: `conic-gradient(#6ab2a7 0deg ${fearIndex.value * 1.8}deg, #e6edf0 ${fearIndex.value * 1.8}deg 180deg, transparent 180deg 360deg)`,
}));

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${Math.round(Number(value) * 100)}%`;
}

function analysisLabel(analysis) {
  return analysis.theme || `분석 ${analysis.analysis_id}`;
}

function recommendationLabel(value) {
  if (value === "BUY") {
    return "매수";
  }
  if (value === "WATCH") {
    return "관찰";
  }
  return value === "ALL" ? "전체" : value;
}

async function fetchJson(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("API 응답을 불러오지 못했습니다.");
    }
    return response.json();
  } catch (error) {
    const demoPayload = getDemoPayload(url);
    if (demoPayload) {
      return demoPayload;
    }
    throw error;
  }
}

function getDemoPayload(url) {
  const analysisMatch = url.match(/\/api\/analyses\/(\d+)\/(recommendations|news)/);

  if (url === "/api/analyses") {
    return { analyses: demoAnalyses, data_source: "static-demo" };
  }

  if (url === "/api/recommendations") {
    return { analysis_id: "all", recommendations: demoRecommendations, data_source: "static-demo" };
  }

  if (url === "/api/analyses/news") {
    return { analysis_id: "all", news_articles: demoNewsArticles, data_source: "static-demo" };
  }

  if (url === "/api/recommendations/latest") {
    return {
      analysis_id: 2,
      recommendations: demoRecommendations.filter((item) => item.analysis_id === 2),
      data_source: "static-demo",
    };
  }

  if (url === "/api/analyses/latest/news") {
    return {
      analysis_id: 2,
      news_articles: demoNewsArticles.filter((item) => item.analysis_id === 2),
      data_source: "static-demo",
    };
  }

  if (analysisMatch) {
    const nextAnalysisId = Number(analysisMatch[1]);
    const resource = analysisMatch[2];
    if (resource === "recommendations") {
      return {
        analysis_id: nextAnalysisId,
        recommendations: demoRecommendations.filter((item) => item.analysis_id === nextAnalysisId),
        data_source: "static-demo",
      };
    }

    return {
      analysis_id: nextAnalysisId,
      news_articles: demoNewsArticles.filter((item) => item.analysis_id === nextAnalysisId),
      data_source: "static-demo",
    };
  }

  return null;
}

async function loadAnalysisData(nextAnalysisId) {
  loading.value = true;
  errorMessage.value = "";
  selectedRecommendation.value = null;

  try {
    const isAll = nextAnalysisId === "all";
    const recommendationsUrl = isAll
      ? "/api/recommendations"
      : nextAnalysisId
      ? `/api/analyses/${nextAnalysisId}/recommendations`
      : "/api/recommendations/latest";
    const newsUrl = isAll
      ? "/api/analyses/news"
      : nextAnalysisId
      ? `/api/analyses/${nextAnalysisId}/news`
      : "/api/analyses/latest/news";

    const [recommendationsData, newsData] = await Promise.all([
      fetchJson(recommendationsUrl),
      fetchJson(newsUrl),
    ]);

    analysisId.value = recommendationsData.analysis_id ?? newsData.analysis_id;
    recommendations.value = recommendationsData.recommendations ?? [];
    newsArticles.value = newsData.news_articles ?? [];
    dataSource.value = recommendationsData.data_source ?? newsData.data_source ?? "-";
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.";
    recommendations.value = [];
    newsArticles.value = [];
    analysisId.value = null;
    dataSource.value = "error";
  } finally {
    loading.value = false;
  }
}

async function loadDashboard() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const analysesData = await fetchJson("/api/analyses");
    analyses.value = analysesData.analyses ?? [];
    dataSource.value = analysesData.data_source ?? dataSource.value;
    await loadAnalysisData("all");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.";
    analyses.value = [];
    await loadAnalysisData(null);
  }
}

function selectAnalysis(event) {
  const nextAnalysisId = event.target.value === "all" ? "all" : Number(event.target.value);
  loadAnalysisData(nextAnalysisId);
}

function selectRecommendation(item) {
  selectedRecommendation.value =
    selectedRecommendation.value?.stock_code === item.stock_code ? null : item;
}

onMounted(loadDashboard);
</script>

<template>
  <main class="page">
    <section class="market-ticker" aria-label="국내주식 시장 정보">
      <div class="ticker-track">
        <div v-for="loop in 2" :key="loop" class="ticker-group">
          <span v-for="item in marketTickerItems" :key="`${loop}-${item.label}`" class="ticker-item">
            <strong>{{ item.label }}</strong>
            <b>{{ item.value }}</b>
            <em>{{ item.change }} <span v-if="item.rate">({{ item.rate }})</span></em>
          </span>
        </div>
      </div>
    </section>

    <header class="hero">
      <div>
        <p class="eyebrow">Stock News Intelligence</p>
        <h1>뉴스 기반 주식 종목 추천</h1>
        <p class="hero-copy">LS증권 뉴스 흐름을 LLM 분석 결과와 연결해 추천 종목과 근거 뉴스를 확인합니다.</p>
      </div>
      <div class="hero-actions">
        <span class="source-badge">{{ dataSource }}</span>
        <button class="refresh-button" type="button" :disabled="loading" @click="loadDashboard">
          새로고침
        </button>
      </div>
    </header>

    <div class="dashboard-grid">
      <aside class="side-market" aria-label="보조 시장 지표">
        <article class="insight-card exchange-card">
          <div class="insight-title">
            <span class="market-icon">₩</span>
            <div>
              <p class="eyebrow">Exchange Rate</p>
              <h2>환율</h2>
            </div>
          </div>
          <div class="exchange-box">
            <span>{{ exchangeRate.symbol }}</span>
            <strong>{{ exchangeRate.value }}</strong>
            <em>{{ exchangeRate.change }} ({{ exchangeRate.rate }})</em>
            <p>{{ exchangeRate.name }}</p>
          </div>
        </article>

        <article class="insight-card fear-card">
          <div class="insight-title">
            <span class="market-icon">!</span>
            <div>
              <p class="eyebrow">Risk Sentiment</p>
              <h2>공포지수</h2>
            </div>
          </div>
          <div class="fear-gauge" :style="fearGaugeStyle">
            <div>
              <strong>{{ fearIndex.value }}</strong>
              <span>{{ fearIndex.status }}</span>
            </div>
          </div>
          <p>{{ fearIndex.label }}</p>
        </article>
      </aside>

      <section class="main-dashboard">
        <section class="control-panel" aria-label="분석 선택과 필터">
          <label>
            <span>분석 결과</span>
            <select :value="analysisId ?? ''" :disabled="loading || analyses.length === 0" @change="selectAnalysis">
              <option value="all">전체</option>
              <option v-for="analysis in analyses" :key="analysis.analysis_id" :value="analysis.analysis_id">
                {{ analysisLabel(analysis) }}
              </option>
            </select>
          </label>

          <div class="filter-group" aria-label="추천 구분 필터">
            <button
              v-for="filter in filters"
              :key="filter"
              type="button"
              :class="{ active: recommendationFilter === filter }"
              @click="recommendationFilter = filter"
            >
              {{ recommendationLabel(filter) }}
            </button>
          </div>
        </section>

        <section class="metrics" aria-label="요약">
          <article>
            <span>분석 번호</span>
            <strong>{{ analysisId === "all" ? "전체" : analysisId ?? "-" }}</strong>
          </article>
          <article>
            <span>분석 테마</span>
            <strong>{{ analysisId === "all" ? "전체" : selectedAnalysis?.theme ?? "-" }}</strong>
          </article>
          <article>
            <span>추천 종목</span>
            <strong>{{ recommendationCount }}</strong>
          </article>
          <article>
            <span>근거 뉴스</span>
            <strong>{{ newsCount }}</strong>
          </article>
        </section>

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <section class="layout">
          <section class="panel">
            <div class="panel-title">
              <p class="eyebrow">Recommendations</p>
              <h2>추천 종목</h2>
            </div>

            <div v-if="loading" class="empty">불러오는 중...</div>
            <div v-else-if="filteredRecommendations.length === 0" class="empty">조건에 맞는 추천 결과가 없습니다.</div>
            <article
              v-for="item in filteredRecommendations"
              v-else
              :key="`${item.analysis_id ?? analysisId}-${item.rank_no}-${item.stock_code}`"
              class="recommendation-card"
              :class="{ selected: selectedRecommendation?.stock_code === item.stock_code }"
              role="button"
              tabindex="0"
              @click="selectRecommendation(item)"
              @keydown.enter="selectRecommendation(item)"
            >
              <div class="rank">#{{ item.rank_no }}</div>
              <div class="card-body">
                <div class="stock-row">
                  <div>
                    <h3>{{ item.stock_name }}</h3>
                    <span>{{ item.theme ? `${item.theme} / ${item.stock_code}` : item.stock_code }}</span>
                  </div>
                  <strong class="tag" :class="item.recommendation.toLowerCase()">
                    {{ recommendationLabel(item.recommendation) }}
                  </strong>
                </div>
                <p>{{ item.reason }}</p>
                <div class="confidence">
                  <span>신뢰도 {{ formatPercent(item.confidence) }}</span>
                  <div>
                    <i :style="{ width: `${Math.max(0, Math.min(1, Number(item.confidence ?? 0))) * 100}%` }"></i>
                  </div>
                </div>
              </div>
            </article>
          </section>

          <section class="panel">
            <div class="panel-title">
              <p class="eyebrow">Source News</p>
              <h2>{{ selectedRecommendation ? `${selectedRecommendation.stock_name} 근거 뉴스` : "분석에 사용된 뉴스" }}</h2>
              <p v-if="selectedRecommendation" class="panel-note">
                선택한 추천 종목은 현재 분석에 연결된 뉴스 묶음을 근거로 생성되었습니다.
              </p>
            </div>

            <div v-if="loading" class="empty">불러오는 중...</div>
            <div v-else-if="newsArticles.length === 0" class="empty">뉴스가 없습니다.</div>
            <article
              v-for="article in newsArticles"
              v-else
              :key="`${article.analysis_id ?? analysisId}-${article.article_id}`"
              class="news-card"
              :class="{ emphasized: selectedRecommendation }"
            >
              <span class="news-meta">
                {{ article.theme ? `${article.theme} / ` : "" }}{{ article.publisher }} / {{ article.published_at }}
              </span>
              <h3>{{ article.title }}</h3>
              <p>{{ article.summary }}</p>
              <a :href="article.url" target="_blank" rel="noreferrer">원문 보기</a>
            </article>
          </section>
        </section>

        <section class="lower-market">
          <article class="insight-card kospi-card">
            <div class="insight-title">
              <span class="market-icon">▥</span>
              <div>
                <p class="eyebrow">Market Chart</p>
                <h2>{{ kospiChart.label }}</h2>
              </div>
            </div>
            <div class="chart-summary">
              <strong>{{ kospiChart.value }}</strong>
              <em>{{ kospiChart.change }} ({{ kospiChart.rate }})</em>
            </div>
            <svg class="kospi-chart" viewBox="0 0 520 200" role="img" aria-label="코스피 샘플 차트">
              <line x1="10" y1="50" x2="510" y2="50"></line>
              <line x1="10" y1="120" x2="510" y2="120"></line>
              <polygon :points="chartAreaPoints"></polygon>
              <polyline :points="chartPoints"></polyline>
            </svg>
          </article>

          <section class="sector-dashboard" aria-label="업종별 등락률 대시보드">
            <div class="sector-header">
              <div>
                <p class="eyebrow">Sector Movement</p>
                <h2>업종별 등락률 대시보드</h2>
              </div>
              <span>마지막 갱신: {{ sectorDashboard.updatedAt }}</span>
            </div>

            <div class="sector-index-row">
              <article>
                <span>코스피</span>
                <strong>{{ sectorDashboard.kospi.value }}</strong>
                <em>{{ sectorDashboard.kospi.change }} {{ sectorDashboard.kospi.point }}</em>
              </article>
              <article>
                <span>코스닥</span>
                <strong>{{ sectorDashboard.kosdaq.value }}</strong>
                <em>{{ sectorDashboard.kosdaq.change }} {{ sectorDashboard.kosdaq.point }}</em>
              </article>
            </div>

            <div class="sector-lists">
              <article class="sector-list strong">
                <h3>강한 업종 TOP 5</h3>
                <ol>
                  <li v-for="(sector, index) in sectorDashboard.strong" :key="sector.name">
                    <span>{{ index + 1 }}</span>
                    <strong>{{ sector.name }}</strong>
                    <em>{{ sector.rate }}</em>
                  </li>
                </ol>
              </article>

              <article class="sector-list weak">
                <h3>약한 업종 WORST 5</h3>
                <ol>
                  <li v-for="(sector, index) in sectorDashboard.weak" :key="sector.name">
                    <span>{{ index + 1 }}</span>
                    <strong>{{ sector.name }}</strong>
                    <em>{{ sector.rate }}</em>
                  </li>
                </ol>
              </article>
            </div>
          </section>
        </section>
      </section>
    </div>
  </main>
</template>
