import React, { useState } from "react";

export function SearchBar({
  query,
  onQueryChange,
  onSearch,
  onReset,
  loading,
  cartCount = 2,
}) {
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !loading) {
      onSearch();
    }
  }

  return (
    <div className="main-search-header-container">
      <div className="search-header-row">
        {/* Brand Logo & Tagline */}
        <div className="brand-logo-area" onClick={onReset} role="button" title="Back to Homepage">
          <div className="brand-logo-text">
            <span className="brand-primary">Shop</span>
            <span className="brand-accent">AI</span>
          </div>
          <span className="brand-subtext">
            Explore <em>Plus</em> ✦
          </span>
        </div>

        {/* Center Prominent Search Bar */}
        <div className="search-input-center-wrapper">
          <div className="search-input-box">
            <span className="search-leading-icon">🔍</span>
            <input
              type="text"
              className="search-input-field"
              placeholder="Search for Products, Brands and More"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />

            {/* Clear button inside input if text exists */}
            {query && (
              <button
                type="button"
                className="search-clear-inline-btn"
                onClick={() => {
                  onQueryChange("");
                  onReset();
                }}
                title="Clear search"
              >
                ✕
              </button>
            )}

            {/* Search Action Button */}
            <button
              type="button"
              className="search-action-btn"
              onClick={() => onSearch()}
              disabled={loading || !query.trim()}
            >
              {loading ? "Searching…" : "Search"}
            </button>
          </div>
        </div>

        {/* Quick Action Buttons on the Right */}
        <div className="header-quick-actions">
          {/* User Account Button */}
          <div className="action-dropdown-wrapper">
            <button
              type="button"
              className="header-action-btn user-btn"
              onClick={() => setAccountMenuOpen(!accountMenuOpen)}
            >
              <span className="action-icon">👤</span>
              <span className="action-text">Sign In ▾</span>
            </button>

            {accountMenuOpen && (
              <div className="action-dropdown-menu">
                <div className="dropdown-header">
                  <strong>Welcome to ShopAI</strong>
                  <p>Access orders & wishlist</p>
                </div>
                <button type="button" className="dropdown-item">📦 Orders & Tracking</button>
                <button type="button" className="dropdown-item">❤️ Wishlist & Saved</button>
                <button type="button" className="dropdown-item">🎁 Rewards Pass</button>
              </div>
            )}
          </div>

          {/* More Options Button */}
          <div className="action-dropdown-wrapper">
            <button
              type="button"
              className="header-action-btn more-btn"
              onClick={() => setMoreMenuOpen(!moreMenuOpen)}
            >
              <span className="action-text">More ▾</span>
            </button>

            {moreMenuOpen && (
              <div className="action-dropdown-menu">
                <button type="button" className="dropdown-item">🔔 Notification Preferences</button>
                <button type="button" className="dropdown-item">🎧 24x7 Customer Care</button>
                <button type="button" className="dropdown-item">🚀 Download Mobile App</button>
              </div>
            )}
          </div>

          {/* Cart Icon with Badge Counter */}
          <button type="button" className="header-action-btn cart-btn" title="View Shopping Cart">
            <div className="cart-icon-container">
              <span className="cart-icon">🛒</span>
              {cartCount > 0 && <span className="cart-badge-counter">{cartCount}</span>}
            </div>
            <span className="action-text">Cart</span>
          </button>
        </div>
      </div>
    </div>
  );
}
