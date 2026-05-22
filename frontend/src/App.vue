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
  background: `conic-gradient(#16805d 0deg ${fearIndex.value * 1.8}deg, #e6edf0 ${fearIndex.value * 1.8}deg 180deg, transparent 180deg 360deg)`,
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

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("API 응답을 불러오지 못했습니다.");
  }
  return response.json();
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
              {{ filter === "ALL" ? "전체" : filter }}
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
                  <strong class="tag" :class="item.recommendation.toLowerCase()">{{ item.recommendation }}</strong>
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
