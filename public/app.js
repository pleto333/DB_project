const state = {
  recommendations: [],
  newsArticles: [],
  analysisId: null,
  dataSource: "loading",
};

const elements = {
  analysisId: document.querySelector("#analysisId"),
  recommendationCount: document.querySelector("#recommendationCount"),
  newsCount: document.querySelector("#newsCount"),
  dataSource: document.querySelector("#dataSource"),
  recommendationList: document.querySelector("#recommendationList"),
  newsList: document.querySelector("#newsList"),
  refreshButton: document.querySelector("#refreshButton"),
  recommendationTemplate: document.querySelector("#recommendationTemplate"),
  newsTemplate: document.querySelector("#newsTemplate"),
};

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${Math.round(Number(value) * 100)}%`;
}

function setStatus(text) {
  elements.dataSource.textContent = text;
}

function clearChildren(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function renderMetrics() {
  elements.analysisId.textContent = state.analysisId ?? "-";
  elements.recommendationCount.textContent = String(state.recommendations.length);
  elements.newsCount.textContent = String(state.newsArticles.length);
  setStatus(state.dataSource === "database" ? "Database" : "Demo");
}

function renderRecommendations() {
  clearChildren(elements.recommendationList);

  if (state.recommendations.length === 0) {
    elements.recommendationList.innerHTML = '<div class="empty">추천 결과가 없습니다.</div>';
    return;
  }

  state.recommendations.forEach((item) => {
    const fragment = elements.recommendationTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".recommendation-card");
    const confidence = Math.max(0, Math.min(1, Number(item.confidence ?? 0)));

    card.querySelector(".rank").textContent = `#${item.rank_no}`;
    card.querySelector("h3").textContent = item.stock_name;
    card.querySelector(".stock-code").textContent = item.stock_code;
    card.querySelector(".tag").textContent = item.recommendation;
    card.querySelector(".reason").textContent = item.reason;
    card.querySelector(".confidence-label").textContent = `신뢰도 ${formatPercent(item.confidence)}`;
    card.querySelector(".confidence-bar").style.width = `${confidence * 100}%`;

    elements.recommendationList.appendChild(fragment);
  });
}

function renderNews() {
  clearChildren(elements.newsList);

  if (state.newsArticles.length === 0) {
    elements.newsList.innerHTML = '<div class="empty">분석에 사용된 뉴스가 없습니다.</div>';
    return;
  }

  state.newsArticles.forEach((item) => {
    const fragment = elements.newsTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".news-card");
    const meta = [item.publisher, item.published_at].filter(Boolean).join(" / ");

    card.querySelector(".news-meta").textContent = meta || item.source || "news";
    card.querySelector("h3").textContent = item.title;
    card.querySelector("p").textContent = item.summary || "";
    card.querySelector("a").href = item.url;

    elements.newsList.appendChild(fragment);
  });
}

function render() {
  renderMetrics();
  renderRecommendations();
  renderNews();
}

async function loadDashboard() {
  setStatus("Loading");
  elements.refreshButton.disabled = true;

  try {
    const [recommendationsResponse, newsResponse] = await Promise.all([
      fetch("/api/recommendations/latest"),
      fetch("/api/analyses/latest/news"),
    ]);

    if (!recommendationsResponse.ok || !newsResponse.ok) {
      throw new Error("API response failed");
    }

    const recommendationsData = await recommendationsResponse.json();
    const newsData = await newsResponse.json();

    state.analysisId = recommendationsData.analysis_id ?? newsData.analysis_id;
    state.recommendations = recommendationsData.recommendations ?? [];
    state.newsArticles = newsData.news_articles ?? [];
    state.dataSource = recommendationsData.data_source ?? newsData.data_source ?? "unknown";
  } catch (error) {
    state.analysisId = null;
    state.recommendations = [];
    state.newsArticles = [];
    state.dataSource = "error";
    console.error(error);
  } finally {
    elements.refreshButton.disabled = false;
    render();
  }
}

elements.refreshButton.addEventListener("click", loadDashboard);
loadDashboard();
