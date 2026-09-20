import React, { useEffect, useState } from "react";
import { TopUtilityBar } from "./components/TopUtilityBar";
import { SearchBar } from "./components/SearchBar";
import { CategoryNavBar } from "./components/CategoryNavBar";
import { HeroPromoBanners } from "./components/HeroPromoBanners";
import { ProductSection } from "./components/ProductSection";
import { ResultsGrid } from "./components/ResultsGrid";
import { fetchDeals, fetchSuggested } from "./services/api";
import { useSearch } from "./hooks/useSearch";

function InferredFilters({ textParse }) {
  if (!textParse) return null;

  const filters = [];
  if (textParse.gender) filters.push({ label: "Audience", value: textParse.gender });
  if (textParse.color) filters.push({ label: "Color", value: textParse.color });
  if (textParse.category_hint) filters.push({ label: "Category", value: textParse.category_hint });
  if (textParse.brand) filters.push({ label: "Brand", value: textParse.brand });
  if (textParse.semantic_query && textParse.semantic_query !== textParse.original_query) {
    filters.push({ label: "Intent", value: textParse.semantic_query });
  }

  if (filters.length === 0) return null;

  return (
    <div className="inferred-filters-bar">
      <span className="filters-label">✨ AI Extracted Attributes:</span>
      <div className="filters-list">
        {filters.map((f, i) => (
          <span key={i} className="filter-pill">
            <span className="filter-tag-label">{f.label}:</span> <strong>{f.value}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}

function DeveloperPanel({ meta, results }) {
  const [open, setOpen] = useState(false);

  if (!meta && !results?.length) return null;

  return (
    <footer className="dev-footer-section">
      <button
        className="dev-toggle-btn"
        type="button"
        onClick={() => setOpen((value) => !value)}
      >
        <span>🛠️ {open ? "Hide" : "Inspect"} Backend Model Signals & Vector Metrics</span>
      </button>

      {open && (
        <div className="dev-details-box">
          {meta?.text_parse && (
            <div className="dev-block">
              <h3>Stage 1: Qwen2.5-0.5B Query Parsing</h3>
              <pre>{JSON.stringify(meta.text_parse, null, 2)}</pre>
            </div>
          )}
          {meta?.vision_parse && (
            <div className="dev-block">
              <h3>Vision Alignment Analysis</h3>
              <pre>{JSON.stringify(meta.vision_parse, null, 2)}</pre>
            </div>
          )}
          {results?.length > 0 && (
            <div className="dev-block">
              <h3>Top-5 Two-Stage Similarity Scores (BGE Dense + CLIP Cross-Modal)</h3>
              <pre>
                {JSON.stringify(
                  results.slice(0, 5).map((item) => ({
                    rank: item.rank,
                    pid: item.pid,
                    bge_dense_score: item.text_score,
                    clip_rerank_score: item.clip_score,
                    final_hybrid_score: item.final_score,
                    retrieved_by: item.retrieved_by,
                  })),
                  null,
                  2
                )}
              </pre>
            </div>
          )}
        </div>
      )}
    </footer>
  );
}

export default function App() {
  const {
    query,
    setQuery,
    imagePreview,
    selectImage,
    clearImage,
    results,
    meta,
    loading,
    loadingMsg,
    error,
    mode,
    runSearch,
    reset,
  } = useSearch();

  const [activeCategory, setActiveCategory] = useState("for-you");
  const [deals, setDeals] = useState([]);
  const [suggested, setSuggested] = useState([]);
  const [cartCount, setCartCount] = useState(2);

  // Load Homepage initial curated feeds
  useEffect(() => {
    fetchDeals(8)
      .then((data) => setDeals(data || []))
      .catch((err) => console.warn("Failed to load deals:", err));

    fetchSuggested(8)
      .then((data) => setSuggested(data || []))
      .catch((err) => console.warn("Failed to load suggested:", err));
  }, []);

  // Handle Find Similar
  function handleFindSimilar(product) {
    const searchTerms = [
      product.main_category,
      product.norm_text ? product.norm_text.split("|")[0].trim() : "",
    ]
      .filter(Boolean)
      .join(" ");
    const finalQ = searchTerms || product.product_name;
    setQuery(finalQ);
    runSearch(10, 0.5, 0.5, finalQ);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Handle Category Selection
  function handleSelectCategory(cat) {
    setActiveCategory(cat.id);
    if (!cat.query) {
      // "For You" resets back to homepage feed
      reset();
    } else {
      setQuery(cat.label);
      runSearch(12, 0.6, 0.4, cat.query);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  // Handle Quick search from banners
  function handleQuickSearch(q) {
    setQuery(q);
    runSearch(10, 0.5, 0.5, q);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const isSearchActive = results !== null || loading;

  return (
    <div className="marketplace-app">
      {/* 1. Top Utility Navigation Bar */}
      <TopUtilityBar cartCount={cartCount} />

      {/* 2. Main Search Header with Brand, Full Search Bar & Actions */}
      <header className="main-sticky-header">
        <div className="header-inner-wrap">
          <SearchBar
            query={query}
            onQueryChange={setQuery}
            onSearch={runSearch}
            onReset={reset}
            loading={loading}
            cartCount={cartCount}
          />
        </div>

        {/* 3. Horizontal Category Navigation Bar */}
        <CategoryNavBar
          activeCategory={activeCategory}
          onSelectCategory={handleSelectCategory}
        />
      </header>

      {/* 4. Main Body Content */}
      <main className="main-content-layout">
        {error && (
          <section className="error-banner" role="alert">
            <div className="error-icon">⚠️</div>
            <div className="error-content">
              <strong>Search Encountered an Issue</strong>
              <p>{error}</p>
            </div>
            <button type="button" className="error-dismiss-btn" onClick={reset}>
              Dismiss
            </button>
          </section>
        )}

        {/* Search Results View */}
        {isSearchActive ? (
          <div className="search-results-container">
            {/* Breadcrumb / Back Bar */}
            <div className="search-breadcrumb-bar">
              <button type="button" className="back-to-home-btn" onClick={reset}>
                ← Back to Home
              </button>
              <span className="breadcrumb-divider">/</span>
              <span className="breadcrumb-current">
                {query ? `Search: "${query}"` : "Search Results"}
              </span>
            </div>

            <InferredFilters textParse={meta?.text_parse} />

            <ResultsGrid
              results={results}
              meta={meta}
              loading={loading}
              loadingMsg={loadingMsg}
              onFindSimilar={handleFindSimilar}
            />

            <DeveloperPanel meta={meta} results={results} />
          </div>
        ) : (
          /* Homepage Default View */
          <div className="homepage-content-container">
            {/* Hero & Promotion Banners Grid */}
            <HeroPromoBanners onQuickSearch={handleQuickSearch} />

            {/* Product Carousels / Sections */}
            <ProductSection
              title="🔥 Deals for You"
              subtitle="Up to 75% off on top lifestyle, footwear & apparel"
              badgeText="Limited Time"
              products={deals}
              onFindSimilar={handleFindSimilar}
              onViewAll={() => handleQuickSearch("Top Deals discount")}
            />

            <ProductSection
              title="✨ Suggested For You"
              subtitle="Curated products across 6,681 AI-verified catalog items"
              badgeText="Recommended"
              products={suggested}
              onFindSimilar={handleFindSimilar}
              onViewAll={() => handleQuickSearch("Popular trending")}
            />
          </div>
        )}
      </main>

      {/* Modern Marketplace Footer */}
      <footer className="marketplace-footer">
        <div className="footer-top-grid">
          <div className="footer-col">
            <h4>ABOUT</h4>
            <ul>
              <li><a href="#about">About ShopAI</a></li>
              <li><a href="#careers">Careers</a></li>
              <li><a href="#press">Press Stories</a></li>
              <li><a href="#corporate">Corporate Information</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>HELP & SUPPORT</h4>
            <ul>
              <li><a href="#payments">Payments</a></li>
              <li><a href="#shipping">Shipping & Delivery</a></li>
              <li><a href="#returns">Cancellation & Returns</a></li>
              <li><a href="#faq">FAQ</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>CONSUMER POLICY</h4>
            <ul>
              <li><a href="#terms">Terms of Use</a></li>
              <li><a href="#security">Security</a></li>
              <li><a href="#privacy">Privacy Policy</a></li>
              <li><a href="#sitemap">E-Commerce Sitemap</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>AI ENGINE INFO</h4>
            <p className="footer-ai-desc">
              Powered by Two-Stage Hybrid Retrieval: Qwen2-VL-2B visual captions, Qwen2.5 SLM query normalization, BGE-Large dense text vectors (FAISS), and OpenAI CLIP ViT-B/32 multimodal cross-reranking.
            </p>
            <div className="footer-vram-tag">6,681 Products • Sub-100ms CUDA Retrieval</div>
          </div>
        </div>
        <div className="footer-bottom-bar">
          <span>© 2026 ShopAI E-Commerce Multimodal Search Engine. All rights reserved.</span>
          <div className="footer-badges">
            <span>🛡️ 100% Authentic Products</span>
            <span>📦 Fast Delivery</span>
            <span>🔒 Secure Payments</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
