import React from "react";

export function HeroPromoBanners({ onQuickSearch }) {
  return (
    <section className="hero-promo-section" aria-label="Featured promotions and deals">
      <div className="hero-banners-grid">
        {/* Main Grand Banner */}
        <div className="hero-banner-card main-promo">
          <div className="banner-content">
            <span className="banner-tag">🌟 MEGA EXPANSION SALE</span>
            <h2>6,881 AI-Indexed Products</h2>
            <p className="banner-subtitle">
              Discover flagship smartphones, designer fashion, accessories & footwear with neural multimodal precision.
            </p>
            <div className="banner-badges">
              <span className="deal-badge">Up to 75% OFF</span>
              <span className="deal-badge gold">🛡️ 100% Genuine Brands</span>
            </div>
            <button
              type="button"
              className="banner-cta-btn primary"
              onClick={() => onQuickSearch("5G mobile phone smartphone")}
            >
              Shop Latest Mobiles →
            </button>
          </div>
          <div className="banner-graphic-wrapper">
            <div className="graphic-circle circle-1"></div>
            <div className="graphic-circle circle-2"></div>
            <div className="floating-tag tag-1">📱 5G Mobiles</div>
            <div className="floating-tag tag-2">👗 Fashion</div>
            <div className="floating-tag tag-3">⌚ Watches</div>
          </div>
        </div>

        {/* Feature Banner 1: Fashion & Apparel */}
        <div className="hero-banner-card feature-promo fashion-promo">
          <div className="banner-content">
            <span className="banner-tag purple">👗 ETHNIC & WESTERN</span>
            <h3>Trending Styles</h3>
            <p>Curated designer shirts, formal trousers, dresses, and ethnic wear.</p>
            <button
              type="button"
              className="banner-cta-btn secondary"
              onClick={() => onQuickSearch("Men formal shirt and women dress")}
            >
              Shop Fashion →
            </button>
          </div>
        </div>

        {/* Feature Banner 2: 5G Smartphones & Mobiles */}
        <div className="hero-banner-card feature-promo accessories">
          <div className="banner-content">
            <span className="banner-tag emerald">📱 200 NEW SMARTPHONES</span>
            <h3>Flagship 5G Mobiles</h3>
            <p>Apple iPhone 15, Samsung Galaxy S23 Ultra, OnePlus, and Moto 5G.</p>
            <button
              type="button"
              className="banner-cta-btn secondary"
              onClick={() => onQuickSearch("5G mobile phone smartphone")}
            >
              Explore Mobiles →
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
