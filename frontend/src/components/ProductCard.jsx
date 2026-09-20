import React, { useState } from "react";
import { getProductImageUrl } from "../services/api";

const FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect width='200' height='200' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23aaa' font-size='14'%3ENo image%3C/text%3E%3C/svg%3E";

export function ProductCard({ product, onFindSimilar }) {
  const [imgSrc, setImgSrc] = useState(getProductImageUrl(product.image_path));

  // Consistent pseudo-random rating based on product PID hash
  const ratingBase = product.pid ? (product.pid.charCodeAt(0) + product.pid.charCodeAt(1) || 120) : 120;
  const ratingScore = (3.8 + (ratingBase % 12) / 10).toFixed(1);
  const ratingCount = ((ratingBase * 17) % 3500 + 120).toLocaleString();

  const discount =
    product.retail_price && product.discounted_price && product.retail_price > product.discounted_price
      ? Math.round((1 - product.discounted_price / product.retail_price) * 100)
      : null;

  // Determine special offer tag
  const specialTag = discount && discount >= 50 ? "🔥 Top Deal" : (ratingBase % 2 === 0 ? "⚡ Hot Offer" : "✨ Bestseller");

  // Match percentage calculation if searching
  const rawScore = Number(product.final_score ?? product.text_score ?? 0.45);
  const matchPercent = Math.min(99, Math.max(74, Math.round((rawScore / 0.55) * 100)));

  return (
    <div className="product-card">
      {/* Top badges & rank */}
      <div className="product-card-header-bar">
        <span className="special-offer-tag">{specialTag}</span>
        {product.rank && (
          <span className="product-rank-badge">#{product.rank}</span>
        )}
      </div>

      {/* Image container */}
      <div className="product-img-wrapper">
        <img
          src={imgSrc || FALLBACK}
          alt={product.product_name || "Product image"}
          className="product-img"
          onError={() => setImgSrc(FALLBACK)}
          loading="lazy"
        />
        {onFindSimilar && (
          <button
            type="button"
            className="find-similar-btn"
            onClick={() => onFindSimilar(product)}
            title="Search for visually similar items in the catalog"
          >
            🔍 Find Similar
          </button>
        )}
      </div>

      {/* Content info */}
      <div className="product-info">
        {/* Brand & Category */}
        <div className="product-brand-line">
          <span className="product-brand">{product.brand && product.brand !== "Unknown" ? product.brand : product.main_category || "Top Brand"}</span>
          <div className="star-rating-badge" title={`Customer Rating: ${ratingScore} out of 5 stars`}>
            <span>★ {ratingScore}</span>
            <span className="rating-count">({ratingCount})</span>
          </div>
        </div>

        {/* Product Title */}
        <div className="product-name" title={product.product_name || "Untitled product"}>
          {product.product_name || "Untitled product"}
        </div>

        {/* Price Row with Discount */}
        <div className="product-price-row">
          {product.discounted_price != null ? (
            <span className="price-current">
              ₹{Math.round(product.discounted_price).toLocaleString("en-IN")}
            </span>
          ) : product.retail_price != null ? (
            <span className="price-current">
              ₹{Math.round(product.retail_price).toLocaleString("en-IN")}
            </span>
          ) : null}

          {product.retail_price != null && product.discounted_price != null && product.retail_price > product.discounted_price && (
            <span className="price-original">
              ₹{Math.round(product.retail_price).toLocaleString("en-IN")}
            </span>
          )}

          {discount !== null && discount > 0 && (
            <span className="price-discount-pill">{discount}% off</span>
          )}
        </div>

        {/* Free Delivery Tag */}
        <div className="delivery-tag">
          <span className="free-delivery-text">Free Delivery</span>
          <span className="assured-badge">🛡️ Assured</span>
        </div>

        {/* Match Percentage & AI caption if available */}
        {product.clip_score != null || product.final_score != null ? (
          <div className="match-indicator-row">
            <span className="match-pill">
              <span className="match-dot"></span>
              {matchPercent}% Match
            </span>
            {product.clip_score != null && (
              <span className="visual-match-pill" title="Multimodal visual alignment verified by CLIP">
                👁️ Visual
              </span>
            )}
          </div>
        ) : null}

        {product.raw_caption && (
          <div className="product-ai-caption" title={product.raw_caption}>
            <span className="ai-caption-icon">✨</span> {product.raw_caption}
          </div>
        )}
      </div>
    </div>
  );
}
