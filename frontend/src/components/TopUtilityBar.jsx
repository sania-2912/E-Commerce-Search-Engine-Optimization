import React, { useState, useEffect } from "react";
import { fetchHealth } from "../services/api";

export function TopUtilityBar({ cartCount = 0 }) {
  const [location, setLocation] = useState("Mumbai 400001");
  const [isEditingLoc, setIsEditingLoc] = useState(false);
  const [health, setHealth] = useState({ state: "checking", message: "Connecting to Engine...", count: 6681 });

  useEffect(() => {
    let active = true;
    const check = () => {
      fetchHealth()
        .then((data) => {
          if (!active) return;
          setHealth({
            state: data?.models_loaded ? "ready" : "loading",
            message: data?.models_loaded
              ? `🟢 ${data?.products_count ? data.products_count.toLocaleString() : "6,681"} Products (RTX 2050 CUDA)`
              : "API reachable, models loading...",
            count: data?.products_count || 6681,
          });
        })
        .catch(() => {
          if (!active) return;
          setHealth({
            state: "offline",
            message: "⚠️ Backend Offline",
            count: 6681,
          });
        });
    };

    check();
    const interval = setInterval(check, 4000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="top-utility-bar">
      <div className="utility-container">
        {/* Left Tagline */}
        <div className="utility-brand-tagline">
          <span className="tagline-icon">🛍️</span>
          <span>Enterprise Multimodal Search Engine • 6,681 Curated Products</span>
        </div>

        {/* Right Location, AI Status, and Indicators */}
        <div className="utility-actions">
          {/* Engine Status Badge */}
          <span className={`engine-badge engine-${health.state}`} title="AI Vector Search Backend Health">
            {health.message}
          </span>

          {/* Location Selector */}
          <div className="location-selector" title="Change delivery location">
            <span className="location-pin">📍</span>
            <span className="deliver-text">Deliver to:</span>
            {isEditingLoc ? (
              <input
                type="text"
                className="location-input"
                value={location}
                autoFocus
                onBlur={() => setIsEditingLoc(false)}
                onKeyDown={(e) => e.key === "Enter" && setIsEditingLoc(false)}
                onChange={(e) => setLocation(e.target.value)}
              />
            ) : (
              <strong className="location-value" onClick={() => setIsEditingLoc(true)}>
                {location} ▾
              </strong>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
