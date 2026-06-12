import React from 'react';

const ButterflyMascot: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <svg className={className} viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bflyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="var(--highlight)" />
          <stop offset="100%" stopColor="var(--accent)" />
        </linearGradient>
        <filter id="bflyGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <style>{`
          .bfly-wing {
            transform-origin: center;
            animation: bflyFlap 0.6s infinite alternate ease-in-out;
          }
          @keyframes bflyFlap {
            0% { transform: scaleX(1); }
            100% { transform: scaleX(0.7); }
          }
        `}</style>
      </defs>
      
      {/* Upper Wings */}
      <path className="bfly-wing" d="M95 90 C 70 30, 20 40, 30 90 C 40 130, 80 110, 95 100 Z" fill="url(#bflyGrad)" opacity="0.9" />
      <path className="bfly-wing" d="M105 90 C 130 30, 180 40, 170 90 C 160 130, 120 110, 105 100 Z" fill="url(#bflyGrad)" opacity="0.9" />
      
      {/* Lower Wings */}
      <path className="bfly-wing" d="M95 100 C 80 110, 40 130, 50 160 C 60 190, 90 150, 95 120 Z" fill="var(--primary)" opacity="0.9" filter="url(#bflyGlow)" />
      <path className="bfly-wing" d="M105 100 C 120 110, 160 130, 150 160 C 140 190, 110 150, 105 120 Z" fill="var(--primary)" opacity="0.9" filter="url(#bflyGlow)" />
      
      {/* Wing Patterns */}
      <circle className="bfly-wing" cx="50" cy="80" r="10" fill="var(--highlight)" />
      <circle className="bfly-wing" cx="150" cy="80" r="10" fill="var(--highlight)" />
      
      {/* Body */}
      <rect x="95" y="70" width="10" height="60" rx="5" fill="#333" />
      
      {/* Head */}
      <circle cx="100" cy="65" r="8" fill="#333" />
      
      {/* Antennae */}
      <path d="M98 60 Q 80 40 75 45" fill="none" stroke="#333" strokeWidth="2" strokeLinecap="round" />
      <path d="M102 60 Q 120 40 125 45" fill="none" stroke="#333" strokeWidth="2" strokeLinecap="round" />
      
      {/* Eyes */}
      <circle cx="97" cy="63" r="1.5" fill="#FFF" />
      <circle cx="103" cy="63" r="1.5" fill="#FFF" />
    </svg>
  );
};

export default ButterflyMascot;
