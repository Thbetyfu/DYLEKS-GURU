import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const ButterflyIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M95 90 C 70 30, 20 40, 30 90 C 40 130, 80 110, 95 100 Z" fill="#ff8a5b" />
    <path d="M105 90 C 130 30, 180 40, 170 90 C 160 130, 120 110, 105 100 Z" fill="#ff8a5b" />
    <path d="M95 100 C 80 110, 40 130, 50 160 C 60 190, 90 150, 95 120 Z" fill="#5b6cff" />
    <path d="M105 100 C 120 110, 160 130, 150 160 C 140 190, 110 150, 105 120 Z" fill="#5b6cff" />
    <circle cx="100" cy="75" r="10" fill="#333" />
    <rect x="96" y="80" width="8" height="50" rx="4" fill="#333" />
  </svg>
);

const BatIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M100 80 Q 50 20 10 50 Q 30 80 15 110 Q 50 100 70 140 Q 80 110 100 110 Z" fill="#7c88ff" />
    <path d="M100 80 Q 150 20 190 50 Q 170 80 185 110 Q 150 100 130 140 Q 120 110 100 110 Z" fill="#7c88ff" />
    <circle cx="100" cy="95" r="22" fill="#25294e" />
    <circle cx="92" cy="94" r="3.5" fill="#ffd166" />
    <circle cx="108" cy="94" r="3.5" fill="#ffd166" />
  </svg>
);

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div
      style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        fontFamily: 'Inter, sans-serif'
      }}
    >
      <span 
        style={{ 
          fontSize: '13px', 
          fontWeight: 'bold', 
          color: isDark ? 'var(--text-muted)' : 'var(--text-main)',
          transition: 'color 0.3s ease',
          opacity: isDark ? 0.6 : 1,
          flexShrink: 0
        }}
      >
        Day
      </span>

      <button
        onClick={toggleTheme}
        aria-label="Toggle Theme"
        style={{
          width: '64px',
          height: '34px',
          minHeight: '34px',
          minWidth: '64px',
          borderRadius: '17px',
          background: isDark ? 'linear-gradient(135deg, #3a416f 0%, #1d2142 100%)' : 'linear-gradient(135deg, #ffd166 0%, #ff8a5b 100%)',
          border: '1.5px solid var(--glass-border)',
          boxShadow: 'var(--glass-shadow), inset 0 2px 4px rgba(0, 0, 0, 0.1)',
          cursor: 'pointer',
          padding: '3px',
          margin: 0,
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          transition: 'background 0.4s ease, border-color 0.4s ease',
          outline: 'none',
          flexShrink: 0
        }}
      >
        {isDark && (
          <div 
            style={{
              position: 'absolute',
              top: 0, left: 0, right: 0, bottom: 0,
              borderRadius: '17px',
              boxShadow: '0 0 12px rgba(124, 136, 255, 0.4)',
              pointerEvents: 'none'
            }}
          />
        )}

        <div
          style={{
            width: '26px',
            height: '26px',
            borderRadius: '50%',
            backgroundColor: '#ffffff',
            boxShadow: '0 3px 8px rgba(0, 0, 0, 0.25), 0 1px 3px rgba(0, 0, 0, 0.15)',
            transform: isDark ? 'translateX(30px)' : 'translateX(0px)',
            transition: 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background-color 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {isDark ? <BatIcon /> : <ButterflyIcon />}
        </div>
      </button>

      <span 
        style={{ 
          fontSize: '13px', 
          fontWeight: 'bold', 
          color: isDark ? 'var(--text-main)' : 'var(--text-muted)',
          transition: 'color 0.3s ease',
          opacity: isDark ? 1 : 0.6,
          flexShrink: 0
        }}
      >
        Night
      </span>
    </div>
  );
};

export default ThemeToggle;
