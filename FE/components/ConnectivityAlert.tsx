import React, { useEffect, useState } from 'react';

const SuccessIcon: React.FC = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="10" fill="#36B37E" />
    <path d="M8 12L11 15L16 9" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const WarningIcon: React.FC = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="10" fill="#FF5630" />
    <path d="M12 8V13M12 16H12.01" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ConnectivityAlert: React.FC = () => {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [localConnected, setLocalConnected] = useState<boolean>(true);
  const [latency, setLatency] = useState<number | null>(null);
  const [showBanner, setShowBanner] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);

  const getBackendUrl = (): string => {
    if (typeof window === 'undefined') return 'http://localhost:3006';
    const savedUrl = localStorage.getItem('api_base_url');
    if (savedUrl) return savedUrl;
    
    // Fallback: Menggunakan hostname yang sama dengan frontend tetapi port backend 3004
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    return `${protocol}//${hostname}:3006`;
  };

  const checkConnection = async () => {
    // 1. Cek status online publik via browser API
    const onlineStatus = window.navigator.onLine;
    setIsOnline(onlineStatus);

    // 2. Cek konektivitas ke server backend lokal
    const backendUrl = getBackendUrl();
    const start = Date.now();
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500); // Timeout 2.5 detik

      const res = await fetch(`${backendUrl}/?cb=${start}`, {
        method: 'GET',
        mode: 'cors',
        cache: 'no-store',
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (res.ok) {
        setLocalConnected(true);
        setLatency(Date.now() - start);
      } else {
        setLocalConnected(false);
        setLatency(null);
      }
    } catch (error) {
      setLocalConnected(false);
      setLatency(null);
    }
  };

  useEffect(() => {
    setMounted(true);
    setIsOnline(window.navigator.onLine);

    // Jalankan pemeriksaan awal
    checkConnection();

    // Event listener untuk status jaringan bawaan browser
    const handleOnline = () => {
      setIsOnline(true);
      checkConnection();
    };
    
    const handleOffline = () => {
      setIsOnline(false);
      checkConnection();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Set interval ping berkala setiap 5 detik ke server lokal
    const intervalId = setInterval(checkConnection, 5000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    // Banner ditampilkan jika:
    // 1. Alat mendeteksi offline publik tapi koneksi lokal aman (mode luring kelas)
    // 2. Alat mendeteksi koneksi lokal terputus (server guru offline/Wi-Fi terputus)
    if (!isOnline && localConnected) {
      setShowBanner(true);
    } else if (!localConnected) {
      setShowBanner(true);
    } else {
      setShowBanner(false);
    }
  }, [isOnline, localConnected]);

  if (!mounted || !showBanner) return null;

  // Tentukan warna tema banner
  const isDanger = !localConnected;
  const bannerBg = isDanger ? 'rgba(255, 86, 48, 0.95)' : 'rgba(54, 179, 126, 0.95)';
  const bannerBorder = isDanger ? 'rgba(255, 86, 48, 0.2)' : 'rgba(54, 179, 126, 0.2)';
  const bannerShadow = isDanger ? '0 10px 30px rgba(255, 86, 48, 0.3)' : '0 10px 30px rgba(54, 179, 126, 0.3)';

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 99999,
        width: '90%',
        maxWidth: '540px',
        padding: '14px 20px',
        background: bannerBg,
        border: `1px solid ${bannerBorder}`,
        borderRadius: '16px',
        boxShadow: bannerShadow,
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        color: '#ffffff',
        fontSize: '14px',
        fontWeight: '600',
        lineHeight: '1.6',
        letterSpacing: '0.02em',
        fontFamily: "'Lexend', 'Inter', system-ui, sans-serif",
        animation: 'slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1) both',
        boxSizing: 'border-box'
      }}
    >
      <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
        {isDanger ? <WarningIcon /> : <SuccessIcon />}
      </div>
      
      <div style={{ flex: 1 }}>
        {isDanger ? (
          <span>
            Koneksi Terputus! Sambungkan kembali perangkat Anda ke Wi-Fi kelas luring DyLeks agar dapat melanjutkan latihan.
          </span>
        ) : (
          <span>
            Jaringan Luring Stabil (Latensi: {latency !== null ? `${latency}ms` : '--'}). Tetap hubungkan Wi-Fi Anda meskipun muncul peringatan "tidak ada internet" dari sistem.
          </span>
        )}
      </div>

      <style jsx global>{`
        @keyframes slideDown {
          from {
            transform: translate(-50%, -40px);
            opacity: 0;
          }
          to {
            transform: translate(-50%, 0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default ConnectivityAlert;
