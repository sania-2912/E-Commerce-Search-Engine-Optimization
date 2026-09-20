import React, { useRef } from "react";

const CATEGORIES = [
  { id: "for-you", label: "For You", icon: "🌟", query: "" },
  { id: "fashion", label: "Fashion", icon: "👗", query: "Fashion clothing dress shirt" },
  { id: "mobiles", label: "Mobiles", icon: "📱", query: "5G mobile phone smartphone" },
  { id: "electronics", label: "Electronics", icon: "💻", query: "Electronics gadgets audio" },
  { id: "beauty", label: "Beauty", icon: "💄", query: "Beauty and Personal Care cosmetics" },
  { id: "home", label: "Home", icon: "🏠", query: "Home Decor and furnishing" },
  { id: "appliances", label: "Appliances", icon: "🔌", query: "Appliances kitchen" },
  { id: "toys", label: "Toys", icon: "🧸", query: "Toys & School Supplies games" },
  { id: "sports", label: "Sports & Fitness", icon: "🏃", query: "Sports & Fitness gym activewear" },
  { id: "furniture", label: "Furniture", icon: "🛋️", query: "Furniture home living" },
  { id: "books", label: "Books", icon: "📚", query: "Books stationery reading" },
  { id: "vehicles", label: "Vehicles", icon: "🚗", query: "Automotive vehicle accessories" },
];

export function CategoryNavBar({ activeCategory, onSelectCategory }) {
  const scrollRef = useRef(null);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = direction === "left" ? -240 : 240;
      scrollRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" });
    }
  };

  return (
    <nav className="category-nav-bar" aria-label="Category navigation">
      <button 
        type="button" 
        className="cat-scroll-arrow left" 
        onClick={() => scroll("left")}
        aria-label="Scroll left"
      >
        ‹
      </button>

      <div className="category-scroll-container" ref={scrollRef}>
        {CATEGORIES.map((cat) => {
          const isActive = activeCategory === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              className={`category-item ${isActive ? "active" : ""}`}
              onClick={() => onSelectCategory(cat)}
            >
              <div className="category-icon-wrapper">
                <span className="category-icon">{cat.icon}</span>
              </div>
              <span className="category-label">{cat.label}</span>
              {isActive && <span className="cat-active-indicator" />}
            </button>
          );
        })}
      </div>

      <button 
        type="button" 
        className="cat-scroll-arrow right" 
        onClick={() => scroll("right")}
        aria-label="Scroll right"
      >
        ›
      </button>
    </nav>
  );
}
