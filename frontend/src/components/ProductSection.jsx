import React, { useRef } from "react";
import { ProductCard } from "./ProductCard";

export function ProductSection({ title, subtitle, badgeText, products = [], onFindSimilar, onViewAll }) {
  const scrollContainerRef = useRef(null);

  const scroll = (direction) => {
    if (scrollContainerRef.current) {
      const scrollAmount = direction === "left" ? -300 : 300;
      scrollContainerRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" });
    }
  };

  if (!products || products.length === 0) return null;

  return (
    <section className="product-section-card">
      <div className="section-header">
        <div className="section-title-group">
          <div className="title-with-badge">
            <h2 className="section-title">{title}</h2>
            {badgeText && <span className="section-badge">{badgeText}</span>}
          </div>
          {subtitle && <p className="section-subtitle">{subtitle}</p>}
        </div>

        <div className="section-actions">
          {onViewAll && (
            <button type="button" className="view-all-btn" onClick={onViewAll}>
              View All →
            </button>
          )}
          <div className="carousel-nav-buttons">
            <button
              type="button"
              className="carousel-arrow"
              onClick={() => scroll("left")}
              aria-label="Previous items"
            >
              ‹
            </button>
            <button
              type="button"
              className="carousel-arrow"
              onClick={() => scroll("right")}
              aria-label="Next items"
            >
              ›
            </button>
          </div>
        </div>
      </div>

      <div className="product-carousel-row" ref={scrollContainerRef}>
        {products.map((item) => (
          <div key={item.pid} className="carousel-product-item">
            <ProductCard product={item} onFindSimilar={onFindSimilar} />
          </div>
        ))}
      </div>
    </section>
  );
}
