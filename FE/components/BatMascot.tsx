import React from 'react';

const BatMascot: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <svg className={className} viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="batWingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#7c88ff" />
          <stop offset="100%" stopColor="#ff76a2" />
        </linearGradient>
        <linearGradient id="batBodyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#41487b" />
          <stop offset="100%" stopColor="#25294e" />
        </linearGradient>
        <filter id="batGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feComponentTransfer in="blur" result="glow">
            <feFuncA type="linear" slope="0.6" />
          </feComponentTransfer>
          <feMerge>
            <feMergeNode in="glow" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <style>{`
          .bat-wing {
            transform-origin: center;
            animation: batFlap 0.8s infinite alternate ease-in-out;
          }
          .bat-ear-l {
            transform-origin: 85px 78px;
            animation: earWiggleL 2s infinite alternate ease-in-out;
          }
          .bat-ear-r {
            transform-origin: 115px 78px;
            animation: earWiggleR 2s infinite alternate ease-in-out;
          }
          @keyframes batFlap {
            0% { transform: scaleY(1); }
            100% { transform: scaleY(0.78); }
          }
          @keyframes earWiggleL {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-5deg); }
          }
          @keyframes earWiggleR {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(5deg); }
          }
        `}</style>
      </defs>

      <path className="bat-wing" d="M100 80 Q 50 20 10 50 Q 30 80 15 110 Q 50 100 70 140 Q 80 110 100 110 Z" fill="url(#batWingGrad)" filter="url(#batGlow)" opacity="0.95" />
      <path className="bat-wing" d="M100 80 Q 150 20 190 50 Q 170 80 185 110 Q 150 100 130 140 Q 120 110 100 110 Z" fill="url(#batWingGrad)" filter="url(#batGlow)" opacity="0.95" />
      
      <g className="bat-ear-l">
        <polygon points="85,78 68,32 93,72" fill="url(#batBodyGrad)" stroke="#7c88ff" strokeWidth="2.5" />
        <polygon points="83,75 73,42 89,70" fill="#ff76a2" opacity="0.85" />
      </g>
      
      <g className="bat-ear-r">
        <polygon points="115,78 132,32 107,72" fill="url(#batBodyGrad)" stroke="#7c88ff" strokeWidth="2.5" />
        <polygon points="117,75 127,42 111,70" fill="#ff76a2" opacity="0.85" />
      </g>
      
      <circle cx="100" cy="95" r="26" fill="url(#batBodyGrad)" stroke="url(#batWingGrad)" strokeWidth="3" filter="url(#batGlow)"/>
      
      <path d="M 82 105 A 18 18 0 0 0 118 105 Z" fill="#7c88ff" opacity="0.3" />

      <circle cx="81" cy="103" r="5" fill="#ff76a2" opacity="0.8" filter="url(#batGlow)" />
      <circle cx="119" cy="103" r="5" fill="#ff76a2" opacity="0.8" filter="url(#batGlow)" />
      
      <circle cx="89" cy="94" r="6" fill="#121620" />
      <circle cx="111" cy="94" r="6" fill="#121620" />
      
      <circle cx="87" cy="92" r="2.2" fill="#FFF" />
      <circle cx="91" cy="96" r="1.0" fill="#FFF" />
      
      <circle cx="109" cy="92" r="2.2" fill="#FFF" />
      <circle cx="113" cy="96" r="1.0" fill="#FFF" />
      
      <path d="M 94 103 Q 100 109 106 103" fill="none" stroke="#FFF" strokeWidth="2" strokeLinecap="round" />
      <polygon points="96,103 99,103 97.5,106.5" fill="#FFF" />
      <polygon points="101,103 104,103 102.5,106.5" fill="#FFF" />
    </svg>
  );
};

export default BatMascot;
