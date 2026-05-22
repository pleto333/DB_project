import { createRequire } from "node:module";
import { mkdir, rm } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import path from "node:path";

const workspace = "C:/Users/tmdql/Desktop/DB_project";
const runtimeRequire = createRequire(
  "C:/Users/tmdql/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/package.json",
);

const tool = await import(pathToFileURL(runtimeRequire.resolve("@oai/artifact-tool")).href);
const skia = await import(pathToFileURL(runtimeRequire.resolve("skia-canvas")).href);

const {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  layers,
  panel,
  text,
  shape,
  chart,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  grow,
  fr,
  auto,
  paint,
  stroke,
  drawSlideToCtx,
} = tool;

const { Canvas, FontLibrary } = skia;

FontLibrary.use("Malgun Gothic", [
  "C:/Windows/Fonts/malgun.ttf",
  "C:/Windows/Fonts/malgunbd.ttf",
  "C:/Windows/Fonts/malgunsl.ttf",
]);

const W = 1920;
const H = 1080;
const FONT = "Malgun Gothic";
const MONO = "Consolas";

const C = {
  bg: "#F7FAF9",
  paper: "#FFFFFF",
  ink: "#0F172A",
  navy: "#111827",
  slate: "#475569",
  muted: "#64748B",
  line: "#D6DEE8",
  teal: "#0F766E",
  mint: "#E5F4EF",
  mint2: "#CFF4E6",
  blue: "#2563EB",
  blueSoft: "#EAF2FF",
  red: "#DC2626",
  redSoft: "#FDECEC",
  green: "#16A34A",
  greenSoft: "#EAF8EF",
  yellow: "#F2C94C",
  yellowSoft: "#FFF7D7",
  code: "#101828",
};

const outDir = path.join(workspace, "output");
const previewDir = path.join(outDir, "ppt_previews");
const pptxPath = path.join(outDir, "stock_news_recommendation_presentation.pptx");

await mkdir(outDir, { recursive: true });
await rm(previewDir, { recursive: true, force: true });
await mkdir(previewDir, { recursive: true });

const presentation = Presentation.create({
  slideSize: { width: W, height: H },
});

const baseStyle = (style = {}) => ({
  typeface: FONT,
  color: C.ink,
  ...style,
});

const monoStyle = (style = {}) => ({
  typeface: MONO,
  color: C.code,
  ...style,
});

function txt(value, opts = {}) {
  return text(value, {
    name: opts.name,
    width: opts.width ?? fill,
    height: opts.height ?? hug,
    columnSpan: opts.columnSpan,
    rowSpan: opts.rowSpan,
    style: baseStyle(opts.style),
  });
}

function codeText(value, opts = {}) {
  return text(value, {
    name: opts.name,
    width: opts.width ?? fill,
    height: opts.height ?? hug,
    style: monoStyle(opts.style),
  });
}

function bgLayer(color = C.bg) {
  return shape({
    name: "slide-bg",
    fill: paint(color),
    width: fixed(W),
    height: fixed(H),
  });
}

function slideRoot(children, opts = {}) {
  return layers(
    { name: "slide-root", width: fill, height: fill },
    [
      bgLayer(opts.bg ?? C.bg),
      column(
        {
          name: "content",
          width: fill,
          height: fill,
          padding: opts.padding ?? { x: 80, y: 64 },
          gap: opts.gap ?? 32,
        },
        children,
      ),
    ],
  );
}

function addSlide(root) {
  const slide = presentation.slides.add();
  slide.compose(root, {
    frame: { left: 0, top: 0, width: W, height: H },
    baseUnit: 8,
  });
  return slide;
}

function eyebrow(label, color = C.teal) {
  return txt(label, {
    width: fill,
    style: {
      fontSize: 19,
      bold: true,
      color,
    },
  });
}

function slideTitle(title, subtitle) {
  return column({ name: "title-stack", width: fill, height: hug, gap: 14 }, [
    eyebrow("DATABASE PROJECT"),
    txt(title, {
      name: "slide-title",
      width: wrap(1450),
      style: { fontSize: 52, bold: true, color: C.ink },
    }),
    subtitle
      ? txt(subtitle, {
          name: "slide-subtitle",
          width: wrap(1320),
          style: { fontSize: 24, color: C.slate },
        })
      : null,
  ].filter(Boolean));
}

function pill(label, opts = {}) {
  return panel(
    {
      name: opts.name,
      fill: paint(opts.fill ?? C.mint),
      line: stroke(opts.line ?? opts.fill ?? C.mint),
      borderRadius: 999,
      padding: { x: opts.x ?? 18, y: opts.y ?? 9 },
      width: hug,
      height: hug,
    },
    txt(label, {
      width: hug,
      style: {
        fontSize: opts.fontSize ?? 18,
        bold: opts.bold ?? true,
        color: opts.color ?? C.teal,
      },
    }),
  );
}

function smallCard(title, body, opts = {}) {
  return panel(
    {
      name: opts.name,
      fill: paint(opts.fill ?? C.paper),
      line: stroke(opts.line ?? C.line),
      borderRadius: opts.radius ?? 18,
      padding: opts.padding ?? { x: 28, y: 24 },
      width: opts.width ?? fill,
      height: opts.height ?? hug,
    },
    column({ width: fill, height: fill, gap: 10 }, [
      txt(title, {
        style: {
          fontSize: opts.titleSize ?? 25,
          bold: true,
          color: opts.titleColor ?? C.ink,
        },
      }),
      txt(body, {
        style: {
          fontSize: opts.bodySize ?? 20,
          color: opts.bodyColor ?? C.slate,
        },
      }),
    ]),
  );
}

function metric(label, value, fillColor, color) {
  return panel(
    {
      fill: paint(fillColor),
      line: stroke(fillColor),
      borderRadius: 18,
      padding: { x: 24, y: 20 },
      width: fill,
      height: fixed(120),
    },
    column({ width: fill, height: fill, gap: 5 }, [
      txt(value, {
        style: { fontSize: 36, bold: true, color },
      }),
      txt(label, {
        style: { fontSize: 17, bold: true, color: C.slate },
      }),
    ]),
  );
}

function arrow(color = C.muted) {
  return txt("→", {
    width: fixed(44),
    style: { fontSize: 34, bold: true, color },
  });
}

function tableBox(title, fields, opts = {}) {
  return panel(
    {
      fill: paint(opts.fill ?? C.paper),
      line: stroke(opts.line ?? C.line),
      borderRadius: 18,
      padding: { x: 18, y: 16 },
      width: opts.width ?? fill,
      height: opts.height ?? fixed(220),
    },
    column({ width: fill, height: fill, gap: 8 }, [
      txt(title, {
        style: {
          fontSize: opts.titleSize ?? 23,
          bold: true,
          color: opts.color ?? C.teal,
        },
      }),
      rule({ stroke: opts.color ?? C.teal, width: fill, weight: 2, opacity: 0.6 }),
      ...fields.map((field) =>
        txt(field, {
          style: { fontSize: opts.fieldSize ?? 15, color: C.slate },
        }),
      ),
    ]),
  );
}

function tableRow(cells, fills = []) {
  return grid(
    {
      width: fill,
      height: hug,
      columns: [fr(0.8), fr(1.05), fr(2.1)],
      columnGap: 8,
      alignItems: "stretch",
    },
    cells.map((cell, idx) =>
      panel(
        {
          fill: paint(fills[idx] ?? C.paper),
          line: stroke(C.line),
          borderRadius: 8,
          padding: { x: 16, y: 13 },
          width: fill,
          height: fill,
        },
        txt(cell, {
          style: {
            fontSize: idx === 2 ? 18 : 19,
            bold: idx < 2,
            color: idx === 0 ? C.teal : C.ink,
          },
        }),
      ),
    ),
  );
}

function makeLineChart() {
  const bars = [
    ["1W", 48],
    ["2W", 62],
    ["3W", 40],
    ["4W", 76],
    ["5W", 92],
    ["6W", 82],
  ];
  return column({ width: fill, height: fixed(138), gap: 8 }, [
    row(
      { width: fill, height: fixed(100), gap: 18, align: "end", justify: "center" },
      bars.map(([, barHeight]) =>
        shape({
          fill: paint(C.green),
          line: stroke(C.green),
          borderRadius: 8,
          width: fixed(46),
          height: fixed(barHeight),
        }),
      ),
    ),
    row(
      { width: fill, height: hug, gap: 22, justify: "center" },
      bars.map(([label]) =>
        txt(label, {
          width: fixed(42),
          style: { fontSize: 13, bold: true, color: C.muted },
        }),
      ),
    ),
  ]);
}

// 1. Cover
addSlide(
  layers({ name: "cover-root", width: fill, height: fill }, [
    bgLayer(C.navy),
    grid(
      {
        name: "cover-grid",
        width: fill,
        height: fill,
        columns: [fr(1.15), fr(0.85)],
        columnGap: 72,
        padding: { x: 92, y: 82 },
        alignItems: "center",
      },
      [
        column({ width: fill, height: hug, gap: 26 }, [
          eyebrow("STOCK NEWS INTELLIGENCE", C.mint2),
          txt("증권사 뉴스 기반\n주식 종목 추천 서비스", {
            width: wrap(980),
            style: {
              fontSize: 64,
              bold: true,
              color: "#FFFFFF",
            },
          }),
          rule({ stroke: C.yellow, width: fixed(180), weight: 5 }),
          txt("뉴스 원본, LLM 분석, 추천 종목을 분리 저장하고\n추천 근거까지 추적 가능한 데이터베이스 구조로 구현", {
            width: wrap(900),
            style: { fontSize: 27, color: "#D9E5E1" },
          }),
          row({ width: fill, height: hug, gap: 14 }, [
            pill("MySQL 3307", { fill: "#173E3A", line: "#23655F", color: "#BFEFE1" }),
            pill("FastAPI JSON", { fill: "#1D334E", line: "#315B87", color: "#D7EAFF" }),
            pill("Vue 임시 화면", { fill: "#3B3114", line: "#6F5A16", color: "#FFF2B6" }),
          ]),
        ]),
        panel(
          {
            fill: paint("#172033"),
            line: stroke("#29364D"),
            borderRadius: 28,
            padding: { x: 34, y: 34 },
            width: fill,
            height: fixed(560),
          },
          column({ width: fill, height: fill, gap: 22 }, [
            txt("TRACEABLE PIPELINE", {
              style: { fontSize: 19, bold: true, color: C.yellow },
            }),
            ...[
              ["1", "뉴스 수집", "LS증권 API에서 기사 원본 저장"],
              ["2", "LLM 분석", "뉴스 묶음을 분석 결과 JSON으로 저장"],
              ["3", "종목 추천", "추천 종목과 이유, 신뢰도 저장"],
              ["4", "화면 표시", "Vue에서 분석별 추천/뉴스 확인"],
            ].map(([num, title, body]) =>
              row({ width: fill, height: hug, gap: 18, align: "center" }, [
                panel(
                  {
                    fill: paint(C.teal),
                    line: stroke(C.teal),
                    borderRadius: 999,
                    padding: { x: 15, y: 10 },
                    width: fixed(50),
                    height: fixed(50),
                    align: "center",
                    justify: "center",
                  },
                  txt(num, {
                    width: hug,
                    style: { fontSize: 22, bold: true, color: "#FFFFFF" },
                  }),
                ),
                column({ width: fill, height: hug, gap: 4 }, [
                  txt(title, { style: { fontSize: 25, bold: true, color: "#FFFFFF" } }),
                  txt(body, { style: { fontSize: 18, color: "#C6D2DF" } }),
                ]),
              ]),
            ),
          ]),
        ),
      ],
    ),
  ]),
);

// 2. Overall flow
addSlide(
  slideRoot([
    slideTitle("전체 시스템 흐름", "뉴스를 먼저 모으고, LLM이 관련 종목을 판단한 뒤, DB에 근거와 결과를 함께 남기는 구조입니다."),
    row(
      {
        name: "pipeline",
        width: fill,
        height: fixed(250),
        gap: 14,
        align: "center",
      },
      [
        smallCard("LS증권 API", "증권사 뉴스 전체 수집", { fill: C.blueSoft, line: "#BFD4FF", titleColor: C.blue, height: fixed(190) }),
        arrow(C.blue),
        smallCard("news_articles", "뉴스 원본 저장\nURL 해시로 중복 방지", { fill: C.paper, height: fixed(190) }),
        arrow(C.teal),
        smallCard("LLM API", "뉴스 흐름 요약\n관련 종목 판단", { fill: C.mint, line: "#BDE8D8", titleColor: C.teal, height: fixed(190) }),
        arrow(C.teal),
        smallCard("DB 저장", "분석 결과와 추천 결과\n근거 뉴스 연결", { fill: C.yellowSoft, line: "#F3DC8D", titleColor: "#8A6500", height: fixed(190) }),
        arrow(C.slate),
        smallCard("Vue 화면", "분석별 추천 종목과\n근거 뉴스 확인", { fill: C.greenSoft, line: "#BEE7C9", titleColor: C.green, height: fixed(190) }),
      ],
    ),
    grid(
      {
        width: fill,
        height: fill,
        columns: [fr(1), fr(1), fr(1)],
        columnGap: 24,
      },
      [
        smallCard("백엔드 역할", "뉴스 수집기 + LLM 분석기 + JSON 응답 서버 역할을 담당합니다.", { height: fixed(160) }),
        smallCard("DB 역할", "뉴스 원본과 분석 결과를 분리해 추천 이유를 나중에 추적할 수 있게 합니다.", { height: fixed(160) }),
        smallCard("프론트 역할", "분석 테마를 선택하고 추천 종목, 신뢰도, 근거 뉴스를 바로 확인합니다.", { height: fixed(160) }),
      ],
    ),
  ]),
);

// 3. DB design goals
addSlide(
  slideRoot([
    slideTitle("DB 설계 목표", "추천 결과만 저장하는 구조가 아니라, 왜 추천되었는지 되돌아볼 수 있는 구조를 목표로 했습니다."),
    grid(
      {
        width: fill,
        height: fill,
        columns: [fr(1), fr(1)],
        rows: [fr(1), fr(1)],
        columnGap: 28,
        rowGap: 28,
      },
      [
        smallCard("01. 뉴스 원본 보존", "LLM에 넣기 전 기사 제목, 요약, URL, 언론사, 발행 시간을 별도 테이블에 저장합니다.", {
          fill: C.paper,
          titleSize: 34,
          bodySize: 23,
        }),
        smallCard("02. 분석 이력 저장", "모델명, 입력 요약, 원본 응답 JSON, 분석 시각을 남겨 같은 뉴스도 다시 비교할 수 있게 했습니다.", {
          fill: C.mint,
          line: "#BDE8D8",
          titleSize: 34,
          bodySize: 23,
        }),
        smallCard("03. 추천 근거 추적", "분석 결과와 사용된 뉴스 기사 사이에 연결 테이블을 두어 추천의 출처를 확인할 수 있습니다.", {
          fill: C.yellowSoft,
          line: "#F0DA88",
          titleSize: 34,
          bodySize: 23,
        }),
        smallCard("04. 중복과 혼합 최소화", "종목, 뉴스, 분석, 추천을 역할별로 분리해 수정/확장 시 영향 범위를 줄였습니다.", {
          fill: C.blueSoft,
          line: "#C7DAFF",
          titleSize: 34,
          bodySize: 23,
        }),
      ],
    ),
  ]),
);

// 4. ERD
addSlide(
  slideRoot([
    slideTitle("ERD 핵심 구조", "뉴스와 분석은 다대다 관계가 될 수 있어서 analysis_news_articles 연결 테이블을 추가했습니다."),
    row({ width: fill, height: fixed(360), gap: 14, align: "center" }, [
      tableBox("news_articles", ["PK article_id", "title / summary", "url_hash UNIQUE", "published_at"], {
        fill: C.blueSoft,
        line: "#C2D7FF",
        color: C.blue,
      }),
      arrow(C.blue),
      tableBox("analysis_news_articles", ["PK analysis_id", "PK article_id", "FK -> llm_analysis", "FK -> news_articles"], {
        fill: C.yellowSoft,
        line: "#F0DA88",
        color: "#8A6500",
        fieldSize: 14,
      }),
      arrow(C.teal),
      column({ width: fill, height: fixed(340), gap: 12 }, [
        tableBox("users", ["PK user_id", "username", "email"], {
          height: fixed(138),
          fill: "#F2F5F9",
          line: "#CED8E6",
          color: C.slate,
          titleSize: 21,
          fieldSize: 13,
        }),
        tableBox("llm_analysis", ["PK analysis_id", "FK user_id", "model_name", "response_json"], {
          height: fixed(188),
          fill: C.mint,
          line: "#BDE8D8",
          color: C.teal,
        }),
      ]),
      arrow(C.teal),
      tableBox("stock_recommendations", ["PK recommendation_id", "FK analysis_id", "FK stock_id", "rank / confidence"], {
        fill: C.redSoft,
        line: "#F7C8C8",
        color: C.red,
        titleSize: 20,
        fieldSize: 14,
      }),
      arrow(C.red),
      tableBox("stocks", ["PK stock_id", "stock_code UNIQUE", "stock_name", "market"], {
        fill: C.greenSoft,
        line: "#BEE7C9",
        color: C.green,
      }),
    ]),
    panel(
      {
        fill: paint(C.paper),
        line: stroke(C.line),
        borderRadius: 18,
        padding: { x: 30, y: 24 },
        width: fill,
        height: fixed(152),
      },
      grid(
        { width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], columnGap: 22 },
        [
          txt("뉴스 기사 1개는 여러 분석에 다시 사용될 수 있음", {
            style: { fontSize: 23, bold: true, color: C.blue },
          }),
          txt("분석 1개는 여러 뉴스 기사를 입력으로 받을 수 있음", {
            style: { fontSize: 23, bold: true, color: C.teal },
          }),
          txt("추천 결과는 분석 결과와 종목을 연결하는 파생 데이터", {
            style: { fontSize: 23, bold: true, color: C.red },
          }),
        ],
      ),
    ),
  ]),
);

// 5. Normalization
addSlide(
  slideRoot([
    slideTitle("정규화 적용 포인트", "수업에서 배운 정규화 관점으로 보면, 원본 엔터티와 파생 엔터티를 분리한 점이 핵심입니다."),
    grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.82), fr(1.55)],
        columnGap: 36,
      },
      [
        column({ width: fill, height: fill, gap: 22 }, [
          smallCard("1NF", "하나의 컬럼에는 하나의 값만 저장", {
            fill: C.blueSoft,
            line: "#C2D7FF",
            titleColor: C.blue,
            height: fixed(140),
          }),
          smallCard("2NF / 3NF", "종목, 뉴스, 분석, 추천을 독립 테이블로 분리", {
            fill: C.mint,
            line: "#BDE8D8",
            titleColor: C.teal,
            height: fixed(158),
          }),
          smallCard("N:M 관계", "뉴스와 분석 사이를 연결 테이블로 표현", {
            fill: C.yellowSoft,
            line: "#F0DA88",
            titleColor: "#8A6500",
            height: fixed(140),
          }),
        ]),
        column({ width: fill, height: fill, gap: 10 }, [
          tableRow(["분류", "테이블", "역할"], [C.navy, C.navy, C.navy]),
          tableRow(["기준 데이터", "users / stocks", "사용자 정보와 추천 가능한 종목 목록을 기준 정보로 관리합니다."]),
          tableRow(["원본 데이터", "news_articles", "LS증권 API로 수집한 기사 원문 정보를 독립적으로 저장합니다."]),
          tableRow(["분석 이력", "llm_analysis", "LLM 입력 요약과 원본 응답 JSON을 저장해 분석 이력을 남깁니다."]),
          tableRow(["연결 데이터", "analysis_news_articles", "한 분석이 어떤 기사들을 사용했는지 다대다 관계를 풀어냅니다."]),
          tableRow(["파생 결과", "stock_recommendations", "LLM 분석 결과로 생성된 추천 종목, 이유, 신뢰도를 저장합니다."]),
        ]),
      ],
    ),
  ]),
);

// 6. Sample data and queries
addSlide(
  slideRoot([
    slideTitle("샘플 데이터와 조회 쿼리", "실제 API/LLM 연결 전에도 DB 구조를 확인할 수 있도록 한국어 샘플 데이터를 넣었습니다."),
    grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.78), fr(1.42)],
        columnGap: 34,
      },
      [
        column({ width: fill, height: fill, gap: 16 }, [
          metric("뉴스 기사", "8건", C.blueSoft, C.blue),
          metric("LLM 분석 결과", "3건", C.mint, C.teal),
          metric("추천 종목", "7건", C.redSoft, C.red),
          metric("뉴스-분석 연결", "8건", C.yellowSoft, "#8A6500"),
          smallCard("분석 테마", "반도체, 2차전지, 플랫폼", {
            fill: C.paper,
            height: fixed(116),
            titleSize: 22,
            bodySize: 20,
          }),
        ]),
        column({ width: fill, height: fill, gap: 18 }, [
          panel(
            {
              fill: paint("#0B1220"),
              line: stroke("#26344D"),
              borderRadius: 18,
              padding: { x: 28, y: 22 },
              width: fill,
              height: fixed(240),
            },
            column({ width: fill, height: fill, gap: 12 }, [
              txt("추천 종목 조회", {
                style: { fontSize: 22, bold: true, color: "#D7EAFF" },
              }),
              codeText(
                `SELECT r.rank_no, s.stock_name, r.recommendation, r.confidence
FROM stock_recommendations r
JOIN stocks s ON r.stock_id = s.stock_id
WHERE r.analysis_id = ?;`,
                { style: { fontSize: 20, color: "#E8F0FF" } },
              ),
            ]),
          ),
          panel(
            {
              fill: paint("#0B1220"),
              line: stroke("#26344D"),
              borderRadius: 18,
              padding: { x: 28, y: 22 },
              width: fill,
              height: fixed(240),
            },
            column({ width: fill, height: fill, gap: 12 }, [
              txt("추천 근거 뉴스 조회", {
                style: { fontSize: 22, bold: true, color: "#D7EAFF" },
              }),
              codeText(
                `SELECT n.title, n.publisher, n.published_at
FROM analysis_news_articles an
JOIN news_articles n ON an.article_id = n.article_id
WHERE an.analysis_id = ?;`,
                { style: { fontSize: 20, color: "#E8F0FF" } },
              ),
            ]),
          ),
          smallCard("발표 시 보여줄 포인트", "Workbench나 SQL 명령으로 테이블 구조와 샘플 데이터를 직접 확인할 수 있고, 같은 데이터를 API와 Vue 화면에서도 조회할 수 있습니다.", {
            fill: C.greenSoft,
            line: "#BEE7C9",
            titleColor: C.green,
            height: fixed(150),
            bodySize: 20,
          }),
        ]),
      ],
    ),
  ]),
);

// 7. Vue result
addSlide(
  slideRoot([
    slideTitle("Vue 화면 구현 결과", "DB 구조가 화면 기능으로 드러나도록 분석 선택, 추천 필터, 근거 뉴스 확인을 넣었습니다."),
    grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.75), fr(1.45)],
        columnGap: 38,
      },
      [
        column({ width: fill, height: fill, gap: 18 }, [
          smallCard("분석 선택", "전체 / 반도체 / 2차전지 / 플랫폼", {
            fill: C.paper,
            titleColor: C.teal,
            height: fixed(128),
          }),
          smallCard("추천 필터", "전체, BUY, WATCH 상태별 조회", {
            fill: C.blueSoft,
            line: "#C2D7FF",
            titleColor: C.blue,
            height: fixed(128),
          }),
          smallCard("근거 뉴스", "추천 종목을 클릭하면 관련 뉴스 영역을 강조", {
            fill: C.yellowSoft,
            line: "#F0DA88",
            titleColor: "#8A6500",
            height: fixed(142),
          }),
          smallCard("시장 정보", "환율/공포지수는 왼쪽, 코스피와 업종 대시보드는 하단 배치", {
            fill: C.greenSoft,
            line: "#BEE7C9",
            titleColor: C.green,
            height: fixed(158),
          }),
        ]),
        panel(
          {
            fill: paint(C.paper),
            line: stroke(C.line),
            borderRadius: 24,
            padding: { x: 28, y: 24 },
            width: fill,
            height: fill,
          },
          column({ width: fill, height: fill, gap: 16 }, [
            row({ width: fill, height: hug, gap: 14, align: "center" }, [
              txt("뉴스 기반 주식 종목 추천", {
                style: { fontSize: 30, bold: true, color: C.ink },
              }),
              pill("data_source: database", { fill: C.mint, line: "#BDE8D8", color: C.teal, fontSize: 16 }),
            ]),
            grid(
              { width: fill, height: fixed(126), columns: [fr(0.8), fr(1), fr(1)], columnGap: 14 },
              [
                panel(
                  { fill: paint("#F8FAFC"), line: stroke(C.line), borderRadius: 16, padding: { x: 18, y: 16 }, width: fill, height: fill },
                  column({ width: fill, height: fill, gap: 8 }, [
                    txt("분석 결과", { style: { fontSize: 17, bold: true, color: C.slate } }),
                    txt("전체", { style: { fontSize: 30, bold: true, color: C.ink } }),
                  ]),
                ),
                metric("추천 종목", "7개", C.mint, C.teal),
                metric("근거 뉴스", "8건", C.blueSoft, C.blue),
              ],
            ),
            grid(
              { width: fill, height: fixed(260), columns: [fr(1), fr(1)], columnGap: 18 },
              [
                panel(
                  { fill: paint("#F8FAFC"), line: stroke(C.line), borderRadius: 18, padding: { x: 20, y: 18 }, width: fill, height: fill },
                  column({ width: fill, height: fill, gap: 12 }, [
                    txt("추천 종목", { style: { fontSize: 23, bold: true, color: C.ink } }),
                    ...[
                      ["삼성전자", "BUY", "0.87"],
                      ["SK하이닉스", "BUY", "0.84"],
                      ["NAVER", "WATCH", "0.72"],
                    ].map(([name, status, score]) =>
                      row({ width: fill, height: hug, gap: 12, align: "center" }, [
                        txt(name, { width: fill, style: { fontSize: 21, bold: true, color: C.ink } }),
                        pill(status, { fill: status === "BUY" ? C.redSoft : C.blueSoft, line: status === "BUY" ? "#F7C8C8" : "#C2D7FF", color: status === "BUY" ? C.red : C.blue, fontSize: 14 }),
                        txt(score, { width: fixed(55), style: { fontSize: 19, bold: true, color: C.slate } }),
                      ]),
                    ),
                  ]),
                ),
                panel(
                  { fill: paint("#F8FAFC"), line: stroke(C.line), borderRadius: 18, padding: { x: 20, y: 18 }, width: fill, height: fill },
                  column({ width: fill, height: fill, gap: 12 }, [
                    txt("근거 뉴스", { style: { fontSize: 23, bold: true, color: C.ink } }),
                    txt("AI 서버 투자 확대로 메모리 반도체 수요 증가 기대", { style: { fontSize: 19, color: C.slate } }),
                    txt("HBM 공급 부족과 데이터센터 증설이 반도체 업황을 견인", { style: { fontSize: 19, color: C.slate } }),
                    txt("클릭한 종목의 근거 뉴스가 강조됨", { style: { fontSize: 18, bold: true, color: C.teal } }),
                  ]),
                ),
              ],
            ),
            grid(
              { width: fill, height: fill, columns: [fr(1.05), fr(0.95)], columnGap: 18 },
              [
                panel(
                  { fill: paint("#F8FAFC"), line: stroke(C.line), borderRadius: 18, padding: { x: 20, y: 18 }, width: fill, height: fill },
                  column({ width: fill, height: fill, gap: 8 }, [
                    row({ width: fill, height: hug, gap: 14, align: "center" }, [
                      txt("코스피 차트", { width: fill, style: { fontSize: 23, bold: true, color: C.ink } }),
                      txt("2,687.45", { width: hug, style: { fontSize: 24, bold: true, color: C.green } }),
                    ]),
                    makeLineChart(),
                  ]),
                ),
                panel(
                  { fill: paint("#F8FAFC"), line: stroke(C.line), borderRadius: 18, padding: { x: 20, y: 18 }, width: fill, height: fill },
                  column({ width: fill, height: fill, gap: 12 }, [
                    txt("업종별 등락률 TOP5", { style: { fontSize: 23, bold: true, color: C.ink } }),
                    ...[
                      ["1", "전자장비와기기", "+8.12%"],
                      ["2", "석유와가스", "+7.37%"],
                      ["3", "건강관리기술", "+7.35%"],
                    ].map(([rank, sector, rate]) =>
                      row({ width: fill, height: hug, gap: 12, align: "center" }, [
                        pill(rank, { fill: C.red, line: C.red, color: "#FFFFFF", fontSize: 14, x: 10, y: 7 }),
                        txt(sector, { width: fill, style: { fontSize: 18, bold: true, color: C.ink } }),
                        txt(rate, { width: fixed(70), style: { fontSize: 16, bold: true, color: C.red } }),
                      ]),
                    ),
                  ]),
                ),
              ],
            ),
          ]),
        ),
      ],
    ),
  ]),
);

const pptxBlob = await PresentationFile.exportPptx(presentation);
await pptxBlob.save(pptxPath);

const previewFiles = [];
for (const [idx, slide] of presentation.slides.items.entries()) {
  const canvas = new Canvas(W, H);
  const ctx = canvas.getContext("2d");
  await drawSlideToCtx(slide, presentation, ctx, []);
  const file = path.join(previewDir, `slide-${String(idx + 1).padStart(2, "0")}.png`);
  await canvas.toFile(file);
  previewFiles.push(file);
}

const thumbW = 480;
const thumbH = 270;
const montage = new Canvas(thumbW * 2, thumbH * 4);
const montageCtx = montage.getContext("2d");
montageCtx.fillStyle = "#F2F5F9";
montageCtx.fillRect(0, 0, thumbW * 2, thumbH * 4);
for (const [idx, file] of previewFiles.entries()) {
  const img = await skia.loadImage(file);
  const x = (idx % 2) * thumbW;
  const y = Math.floor(idx / 2) * thumbH;
  montageCtx.drawImage(img, x, y, thumbW, thumbH);
}
const montagePath = path.join(previewDir, "montage.png");
await montage.toFile(montagePath);

console.log(JSON.stringify({ pptxPath, previewDir, previewFiles, montagePath }, null, 2));
