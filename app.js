// ================================================================
// Quran Ayah Confusability — Web Client (v0.2 - Network Optimized)
// ================================================================

const SURAH_NAMES = {
    1: "الفاتحة", 2: "البقرة", 3: "آل عمران", 4: "النساء", 5: "المائدة",
    6: "الأنعام", 7: "الأعراف", 8: "الأنفال", 9: "التوبة", 10: "يونس",
    11: "هود", 12: "يوسف", 13: "الرعد", 14: "إبراهيم", 15: "الحجر",
    16: "النحل", 17: "الإسراء", 18: "الكهف", 19: "مريم", 20: "طه",
    21: "الأنبياء", 22: "الحج", 23: "المؤمنون", 24: "النور", 25: "الفرقان",
    26: "الشعراء", 27: "النمل", 28: "القصص", 29: "العنكبوت", 30: "الروم",
    31: "لقمان", 32: "السجدة", 33: "الأحزاب", 34: "سبأ", 35: "فاطر",
    36: "يس", 37: "الصافات", 38: "ص", 39: "الزمر", 40: "غافر",
    41: "فصلت", 42: "الشورى", 43: "الزخرف", 44: "الدخان", 45: "الجاثية",
    46: "الأحقاف", 47: "محمد", 48: "الفتح", 49: "الحجرات", 50: "ق",
    51: "الذاريات", 52: "الطور", 53: "النجم", 54: "القمر", 55: "الرحمن",
    56: "الواقعة", 57: "الحديد", 58: "المجادلة", 59: "الحشر", 60: "الممتحنة",
    61: "الصف", 62: "الجمعة", 63: "المنافقون", 64: "التغابن", 65: "الطلاق",
    66: "التحريم", 67: "الملك", 68: "القلم", 69: "الحاقة", 70: "المعارج",
    71: "نوح", 72: "الجن", 73: "المزمل", 74: "المدثر", 75: "القيامة",
    76: "الإنسان", 77: "المرسلات", 78: "النبأ", 79: "النازعات", 80: "عبس",
    81: "التكوير", 82: "الانفطار", 83: "المطففين", 84: "الانشقاق", 85: "البروج",
    86: "الطارق", 87: "الأعلى", 88: "الغاشية", 89: "الفجر", 90: "البلد",
    91: "الشمس", 92: "الليل", 93: "الضحى", 94: "الشرح", 95: "التين",
    96: "العلق", 97: "القدر", 98: "البينة", 99: "الزلزلة", 100: "العاديات",
    101: "القارعة", 102: "التكاثر", 103: "العصر", 104: "الهمزة", 105: "الفيل",
    106: "قريش", 107: "الماعون", 108: "الكوثر", 109: "الكافرون", 110: "النصر",
    111: "المسد", 112: "الإخلاص", 113: "الفلق", 114: "الناس"
};

// ----------------------------------------------------------------
// State
// ----------------------------------------------------------------
let allData = [];          // raw minified JSON (all 6236)
let idMap = {};            // ayah_id -> record
let displayData = [];      // deduplicated list for explorer
let filteredData = [];     // after search/tier/sort
let currentPage = 1;
const PAGE_SIZE = 20;

// ----------------------------------------------------------------
// DOM Refs
// ----------------------------------------------------------------
const searchInput     = document.getElementById('search-input');
const clearSearchBtn  = document.getElementById('clear-search');
const tierSelect      = document.getElementById('tier-select');
const sortSelect      = document.getElementById('sort-select');
const cardsGrid       = document.getElementById('cards-grid');
const displayedCountEl = document.getElementById('displayed-count');
const totalCountEl    = document.getElementById('total-count');
const prevPageBtn     = document.getElementById('prev-page');
const nextPageBtn     = document.getElementById('next-page');
const pageIndicatorEl = document.getElementById('page-indicator');
const tempSlider      = document.getElementById('temp-slider');
const tempValEl       = document.getElementById('temp-val');
const tempHintEl      = document.getElementById('temp-hint');
const drawPromptBtn   = document.getElementById('draw-prompt-btn');
const sampledContainer= document.getElementById('sampled-card-container');
const sampledContent  = document.getElementById('sampled-card-content');
const leaderboardBody = document.getElementById('leaderboard-body');

// ----------------------------------------------------------------
// Bootstrap
// ----------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadData();
});

// ----------------------------------------------------------------
// Tab Navigation
// ----------------------------------------------------------------
function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(tc => tc.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        });
    });
}

// ----------------------------------------------------------------
// Load & Preprocess Data (Minified Schema: i, s, n, t, w, m, f, p, c)
// ----------------------------------------------------------------
async function loadData() {
    try {
        const res = await fetch('dist/quran_confusability_scores.min.json');
        allData = await res.json();

        // Build id → record lookup (key 'i' = ayah_id)
        allData.forEach(a => { idMap[a.i] = a; });

        // Deduplicate: keep only first occurrence of each unique ayah text
        const seenTexts = new Set();
        displayData = [];
        const corpusOrdered = [...allData].sort((a, b) => (a.s - b.s) || (a.n - b.n));

        for (const item of corpusOrdered) {
            const normKey = item.t.trim().replace(/\s+/g, ' ');
            if (!seenTexts.has(normKey)) {
                seenTexts.add(normKey);
                displayData.push(item);
            }
        }

        totalCountEl.textContent = displayData.length.toLocaleString();

        setupEventListeners();
        filterAndRender();
        renderLeaderboard();

    } catch (err) {
        console.error(err);
        cardsGrid.innerHTML = `<div class="loading-state" style="color:var(--accent-red)">تعذّر تحميل ملف البيانات. تأكد من وجود ملف البيانات في مجلد dist.</div>`;
    }
}

// ----------------------------------------------------------------
// Event Listeners
// ----------------------------------------------------------------
function setupEventListeners() {
    searchInput.addEventListener('input', () => { currentPage = 1; filterAndRender(); });
    clearSearchBtn.addEventListener('click', () => { searchInput.value = ''; currentPage = 1; filterAndRender(); });
    tierSelect.addEventListener('change', () => { currentPage = 1; filterAndRender(); });
    sortSelect.addEventListener('change', () => { currentPage = 1; filterAndRender(); });

    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; renderExplorer(); scrollToTop(); }
    });
    nextPageBtn.addEventListener('click', () => {
        if (currentPage < maxPage()) { currentPage++; renderExplorer(); scrollToTop(); }
    });

    // Simulator
    tempSlider.addEventListener('input', e => {
        const v = parseFloat(e.target.value).toFixed(1);
        tempValEl.textContent = v;
        if (v <= 0.5)      tempHintEl.textContent = 'تركيز شديد على أصعب الآيات تشابهاً';
        else if (v <= 2.0) tempHintEl.textContent = 'توزيع متوازن';
        else               tempHintEl.textContent = 'اختيار شبه عشوائي';
    });

    drawPromptBtn.addEventListener('click', drawSimulatorPrompt);
}

function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }); }
function maxPage() { return Math.max(1, Math.ceil(filteredData.length / PAGE_SIZE)); }

// Arabic Normalization for resilient search
function normalizeArabic(text) {
    if (!text) return '';
    return text
        .normalize('NFKD')
        .replace(/[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]/g, '')
        .replace(/[\u0622\u0623\u0625\u0671]/g, '\u0627')
        .replace(/\u0649/g, '\u064A')
        .replace(/\u0629/g, '\u0647')
        .toLowerCase();
}

function normalizeDigits(str) {
    if (!str) return '';
    return str.replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
}

// ----------------------------------------------------------------
// Filter, Sort, Render
// ----------------------------------------------------------------
function filterAndRender() {
    const rawQuery = searchInput.value.trim();
    const tier     = tierSelect.value;
    const sort     = sortSelect.value;

    // 1. When searching, use full allData so repeated ayahs across surahs are all shown.
    //    When browsing (no query), use deduplicated displayData.
    const sourcePool = rawQuery ? allData : displayData;

    // Sort pool by final_score ('f') descending for tier slicing
    const byScore = [...sourcePool].sort((a, b) => b.f - a.f);
    const N = byScore.length;
    const chunk = Math.floor(N / 5);

    let pool = byScore;
    if (tier === 'tier1') pool = byScore.slice(0, chunk);
    else if (tier === 'tier2') pool = byScore.slice(chunk, 2 * chunk);
    else if (tier === 'tier3') pool = byScore.slice(2 * chunk, 3 * chunk);
    else if (tier === 'tier4') pool = byScore.slice(3 * chunk, 4 * chunk);
    else if (tier === 'tier5') pool = byScore.slice(4 * chunk);

    // 2. Diacritic-insensitive Search filter
    if (rawQuery) {
        const cleanQuery = normalizeArabic(normalizeDigits(rawQuery));
        pool = pool.filter(item => {
            const cleanText = normalizeArabic(item.t);
            const surahName = SURAH_NAMES[item.s] || '';
            const cleanSurahName = normalizeArabic(surahName);
            const ayahId = normalizeDigits(item.i).toLowerCase();

            return ayahId.includes(cleanQuery)
                || cleanSurahName.includes(cleanQuery)
                || cleanText.includes(cleanQuery);
        });
    }

    // 3. Sort
    pool.sort((a, b) => {
        switch (sort) {
            case 'score_desc':     return b.f - a.f;
            case 'score_asc':      return a.f - b.f;
            case 'max_comp_desc':  return b.m - a.m;
            case 'words_asc':      return a.w - b.w;
            case 'words_desc':     return b.w - a.w;
            case 'order':          return (a.s - b.s) || (a.n - b.n);
            default: return 0;
        }
    });

    filteredData = pool;
    renderExplorer();
}

// ----------------------------------------------------------------
// Render Explorer
// ----------------------------------------------------------------
function renderExplorer() {
    displayedCountEl.textContent = filteredData.length.toLocaleString();

    const mp = maxPage();
    if (currentPage > mp) currentPage = mp;

    pageIndicatorEl.textContent = `الصفحة ${currentPage} من ${mp}`;
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = currentPage === mp;

    const slice = filteredData.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

    if (slice.length === 0) {
        cardsGrid.innerHTML = `<div class="loading-state">لا توجد نتائج مطابقة.</div>`;
        return;
    }

    cardsGrid.innerHTML = slice.map(item => buildCard(item)).join('');
    attachToggleListeners();
}

// ----------------------------------------------------------------
// Build a single Ayah card HTML
// ----------------------------------------------------------------
function buildCard(item) {
    const surahName = SURAH_NAMES[item.s] || `سورة ${item.s}`;
    const scoreLabel = formatScore(item.f);
    const tierLabel  = getTierLabel(item.f);
    const tierClass  = getTierClass(item.f);

    // Unique competitors (deduplicate by text)
    const uniqueComps = deduplicateCompetitors(item.c || []);

    const compsHTML = uniqueComps.map((comp, i) => {
        const compRecord = idMap[comp.i];
        const compText   = compRecord ? compRecord.t : '—';
        const compSurah  = compRecord ? (SURAH_NAMES[compRecord.s] || `سورة ${compRecord.s}`) : '';
        const compAyahNum = compRecord ? compRecord.n : '';

        const ngramsHTML = (comp.n || []).map(ng =>
            `<span class="ngram-tag">${ng}</span>`
        ).join('');

        return `
        <div class="competitor-item">
            <div class="comp-header">
                <div class="comp-location">
                    <span class="comp-num">${i + 1}</span>
                    <span class="comp-surah-label">سورة ${compSurah} — الآية ${compAyahNum}</span>
                </div>
                <span class="comp-score-badge">${comp.s.toFixed(1)}</span>
            </div>
            <div class="comp-quran-text">${compText}</div>
            ${ngramsHTML ? `
            <div class="comp-ngrams-row">
                <span class="ngrams-label">عبارات مشتركة:</span>
                <div class="shared-ngrams">${ngramsHTML}</div>
            </div>` : ''}
        </div>`;
    }).join('');

    const cardId = item.i.replace(':', '-');

    return `
    <article class="ayah-card">
        <div class="ayah-card-header">
            <div class="ayah-location">
                <span class="surah-name">سورة ${surahName}</span>
                <span class="ayah-num-badge">آية ${item.n}</span>
            </div>
            <span class="tier-badge ${tierClass}">${tierLabel}</span>
        </div>

        <div class="quran-text">${item.t}</div>

        <div class="metrics-row">
            <div class="metric-pill">
                <span class="metric-label">درجة الصعوبة</span>
                <strong class="metric-val gold">${scoreLabel}</strong>
            </div>
            <div class="metric-pill">
                <span class="metric-label">عدد الكلمات</span>
                <strong class="metric-val">${item.w}</strong>
            </div>
            <div class="metric-pill">
                <span class="metric-label">أقوى منافس</span>
                <strong class="metric-val">${item.m.toFixed(1)}</strong>
            </div>
            <div class="metric-pill">
                <span class="metric-label">احتمال الاختيار</span>
                <strong class="metric-val">${(item.p * 100).toFixed(3)}٪</strong>
            </div>
        </div>

        ${uniqueComps.length > 0 ? `
        <div class="competitors-wrapper">
            <button class="toggle-competitors-btn" data-target="comp-${cardId}">
                <span>آيات قد تُشكل التباساً (${uniqueComps.length})</span>
                <span class="arrow-icon">▾</span>
            </button>
            <div id="comp-${cardId}" class="competitors-list">
                ${compsHTML}
            </div>
        </div>` : ''}
    </article>`;
}

// Remove competitors with duplicate original text
function deduplicateCompetitors(competitors) {
    const seen = new Set();
    const result = [];
    for (const comp of competitors) {
        const rec = idMap[comp.i];
        const key = rec ? rec.t.trim() : comp.i;
        if (!seen.has(key)) {
            seen.add(key);
            result.push(comp);
        }
    }
    return result;
}

function attachToggleListeners() {
    document.querySelectorAll('.toggle-competitors-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const list  = document.getElementById(btn.dataset.target);
            const arrow = btn.querySelector('.arrow-icon');
            if (!list) return;
            list.classList.toggle('open');
            arrow.textContent = list.classList.contains('open') ? '▴' : '▾';
        });
    });
}

// ----------------------------------------------------------------
// Score Helpers
// ----------------------------------------------------------------
function formatScore(s) { return s.toFixed(1); }

let _tierBounds = null;
function getTierBounds() {
    if (_tierBounds) return _tierBounds;
    const sorted = [...displayData].map(d => d.f).sort((a, b) => b - a);
    const N = sorted.length;
    _tierBounds = [
        sorted[Math.floor(N * 0.20)],
        sorted[Math.floor(N * 0.40)],
        sorted[Math.floor(N * 0.60)],
        sorted[Math.floor(N * 0.80)],
    ];
    return _tierBounds;
}

function getTierLabel(score) {
    const [t1, t2, t3, t4] = getTierBounds();
    if (score >= t1) return 'شديد التشابه';
    if (score >= t2) return 'عالي التشابه';
    if (score >= t3) return 'متوسط';
    if (score >= t4) return 'منخفض';
    return 'نادر التشابه';
}

function getTierClass(score) {
    const [t1, t2, t3, t4] = getTierBounds();
    if (score >= t1) return 'tier-extreme';
    if (score >= t2) return 'tier-high';
    if (score >= t3) return 'tier-medium';
    if (score >= t4) return 'tier-low';
    return 'tier-verylow';
}

// ----------------------------------------------------------------
// Simulator
// ----------------------------------------------------------------
function drawSimulatorPrompt() {
    if (displayData.length === 0) return;

    const T = parseFloat(tempSlider.value);
    const rawScores = displayData.map(a => a.f);
    const minScore  = Math.min(...rawScores);
    const maxScore  = Math.max(...rawScores);
    const range     = maxScore - minScore || 1;

    const normScores = rawScores.map(s => (s - minScore) / range);
    const expScores  = normScores.map(s => Math.exp((s - 1) / T));
    const sumExp     = expScores.reduce((acc, v) => acc + v, 0);
    const probs      = expScores.map(v => v / sumExp);

    let rand = Math.random();
    let selectedIdx = probs.length - 1;
    for (let i = 0; i < probs.length; i++) {
        rand -= probs[i];
        if (rand <= 0) { selectedIdx = i; break; }
    }

    const item = displayData[selectedIdx];

    sampledContainer.classList.remove('hidden');
    sampledContent.innerHTML = '';
    void sampledContainer.offsetWidth;

    sampledContent.innerHTML = buildCard(item);
    sampledContainer.classList.add('pop-in');
    sampledContainer.addEventListener('animationend', () => {
        sampledContainer.classList.remove('pop-in');
    }, { once: true });

    attachToggleListeners();
    sampledContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ----------------------------------------------------------------
// Leaderboard
// ----------------------------------------------------------------
function renderLeaderboard() {
    const groups = {};
    allData.forEach(item => {
        if (!groups[item.s]) groups[item.s] = [];
        groups[item.s].push(item);
    });

    const stats = Object.entries(groups).map(([surahId, ayahs]) => {
        const avgScore  = ayahs.reduce((s, a) => s + a.f, 0) / ayahs.length;
        const maxAyah   = ayahs.reduce((prev, cur) => cur.f > prev.f ? cur : prev);
        const totalWords= ayahs.reduce((s, a) => s + a.w, 0);
        return {
            surah_id:   parseInt(surahId),
            surah_name: SURAH_NAMES[surahId] || `سورة ${surahId}`,
            count:      ayahs.length,
            total_words:totalWords,
            avg_score:  avgScore,
            max_ayah:   maxAyah
        };
    });

    stats.sort((a, b) => b.avg_score - a.avg_score);

    leaderboardBody.innerHTML = stats.map((s, idx) => {
        const tierClass = idx < 10 ? 'tier-extreme' : idx < 30 ? 'tier-high' : idx < 70 ? 'tier-medium' : 'tier-low';
        return `
        <tr>
            <td><strong>${idx + 1}</strong></td>
            <td class="surah-cell">سورة ${s.surah_name}</td>
            <td>${s.count}</td>
            <td>${s.total_words.toLocaleString()}</td>
            <td><span class="tier-badge ${tierClass}">${s.avg_score.toFixed(1)}</span></td>
            <td>
                <span class="lb-best-ayah">${s.max_ayah.t.slice(0, 50)}${s.max_ayah.t.length > 50 ? '...' : ''}</span>
                <span class="lb-ayah-id">(${s.max_ayah.i})</span>
            </td>
        </tr>`;
    }).join('');
}
