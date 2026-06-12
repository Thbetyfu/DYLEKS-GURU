import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import styles from '../styles/Home.module.css';
import { useTheme } from '../contexts/ThemeContext';
import BatMascot from '../components/BatMascot';
import ButterflyMascot from '../components/ButterflyMascot';
import ThemeToggle from '../components/ThemeToggle';
import { QRCodeSVG } from 'qrcode.react';

interface Child {
  id: string;
  name: string;
  age: number | null;
  gender: string | null;
  grade: string | null;
  current_level: number;
  risk_score: number;
  risk_level: string;
  teacher_notes: string | null;
}

export default function Dashboard() {
  const router = useRouter();
  const { theme } = useTheme();

  // Auth States
  const [teacherToken, setTeacherToken] = useState<string | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [schoolName, setSchoolName] = useState('');
  const [schoolRegion, setSchoolRegion] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);

  // Student Profiles Data States
  const [children, setChildren] = useState<Child[]>([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [selectedChild, setSelectedChild] = useState<Child | null>(null);

  // Modal States
  const [showQrModal, setShowQrModal] = useState(false);

  // QR & Polling States
  const [qrToken, setQrToken] = useState<string | null>(null);
  const [qrStatus, setQrStatus] = useState<string>('');
  const [connectedStudentName, setConnectedStudentName] = useState<string | null>(null);
  const [qrLoading, setQrLoading] = useState(false);
  const [selectedQrChildId, setSelectedQrChildId] = useState<string | null>(null);

  // Edit Note States
  const [editingNotes, setEditingNotes] = useState('');
  const [notesSaving, setNotesSaving] = useState(false);
  const [generatingRec, setGeneratingRec] = useState(false);

  // Psychologist Recommendations States
  const [psyRecommendations, setPsyRecommendations] = useState<any[]>([]);
  const [loadingPsyRecommendations, setLoadingPsyRecommendations] = useState(false);

  // Learning Sessions States
  const [learningSessions, setLearningSessions] = useState<any[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [activeTab, setActiveTab] = useState<'profile' | 'exercises'>('profile');

  const fetchPsyRecommendations = async (childId: string, token: string) => {
    setLoadingPsyRecommendations(true);
    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/children/${childId}/recommendations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPsyRecommendations(data);
      } else {
        setPsyRecommendations([]);
      }
    } catch (err) {
      console.error('Gagal mengambil rekomendasi psikolog:', err);
      setPsyRecommendations([]);
    } finally {
      setLoadingPsyRecommendations(false);
    }
  };

  const fetchLearningSessions = async (childId: string, token: string) => {
    setLoadingSessions(true);
    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/children/${childId}/learning-sessions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setLearningSessions(data);
      } else {
        setLearningSessions([]);
      }
    } catch (err) {
      console.error('Gagal mengambil riwayat latihan:', err);
      setLearningSessions([]);
    } finally {
      setLoadingSessions(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('teacher_token');
    if (token) {
      setTeacherToken(token);
      fetchChildren(token);
    }
  }, []);

  // Login Guru
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        throw new Error('Username atau password salah.');
      }

      const data = await res.json();
      localStorage.setItem('teacher_token', data.access_token);
      setTeacherToken(data.access_token);
      fetchChildren(data.access_token);
    } catch (err: any) {
      setAuthError(err.message || 'Gagal login.');
    }
  };

  // Register Guru
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          password,
          full_name: fullName,
          school_name: schoolName,
          school_region: schoolRegion,
        }),
      });

      if (!res.ok) {
        throw new Error('Gagal mendaftar. Username mungkin sudah digunakan.');
      }

      // Login otomatis
      const loginRes = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await loginRes.json();
      localStorage.setItem('teacher_token', data.access_token);
      setTeacherToken(data.access_token);
      fetchChildren(data.access_token);
    } catch (err: any) {
      setAuthError(err.message || 'Gagal registrasi.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('teacher_token');
    setTeacherToken(null);
    setChildren([]);
    setSelectedChild(null);
    setQrToken(null);
  };

  // Fetch daftar anak
  const fetchChildren = async (token: string) => {
    setLoadingStudents(true);
    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/children`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setChildren(data);
      }
    } catch (err) {
      console.error('Gagal mengambil daftar anak:', err);
    } finally {
      setLoadingStudents(false);
    }
  };



  // Update Catatan Guru (Orton-Gillingham)
  const handleSaveNotes = async () => {
    if (!teacherToken || !selectedChild) return;
    setNotesSaving(true);
    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/children/${selectedChild.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${teacherToken}`,
        },
        body: JSON.stringify({
          name: selectedChild.name,
          age: selectedChild.age,
          gender: selectedChild.gender,
          grade: selectedChild.grade,
          teacher_notes: editingNotes,
        }),
      });

      if (!res.ok) throw new Error('Gagal memperbarui catatan.');

      const updated = await res.json();
      setSelectedChild(updated);
      
      // Update data di state list agar ter-sinkron
      setChildren(children.map(c => c.id === updated.id ? updated : c));
      alert('Catatan intervensi pedagogis berhasil disimpan secara aman.');
    } catch (err: any) {
      alert(err.message || 'Gagal menyimpan catatan.');
    } finally {
      setNotesSaving(false);
    }
  };

  // Generate Orton-Gillingham Recommendation dynamically via local AI
  const handleGenerateOgRecommendation = async () => {
    if (!selectedChild || !teacherToken) return;
    setGeneratingRec(true);
    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/children/${selectedChild.id}/recommend-og`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${teacherToken}`,
        },
      });

      if (!res.ok) {
        throw new Error('Gagal memanggil modul rekomendasi AI luring.');
      }

      const data = await res.json();
      const newRec = data.recommendation;
      
      // Overwrite or append with a clean double newline separator
      const mergedNotes = editingNotes 
        ? `${editingNotes}\n\n[Rencana Intervensi Orton-Gillingham AI]\n${newRec}`
        : `[Rencana Intervensi Orton-Gillingham AI]\n${newRec}`;
      
      setEditingNotes(mergedNotes);
    } catch (err: any) {
      alert(err.message || 'Gagal membuat rekomendasi intervensi. Pastikan uvicorn dan Ollama Anda aktif.');
    } finally {
      setGeneratingRec(false);
    }
  };

  // Hapus Siswa
  const handleDeleteStudent = async (id: string) => {
    if (!teacherToken) return;
    if (!confirm('Apakah Anda yakin ingin menghapus profil siswa ini beserta seluruh riwayat skrining & latihan? Tindakan ini tidak bisa dibatalkan.')) return;

    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/children/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${teacherToken}` },
      });

      if (!res.ok) throw new Error('Gagal menghapus profil.');

      if (selectedChild?.id === id) {
        setSelectedChild(null);
      }
      fetchChildren(teacherToken);
    } catch (err: any) {
      alert(err.message || 'Gagal menghapus.');
    }
  };

  // Generate QR Token
  const triggerQrModal = async (childId: string | null) => {
    if (!teacherToken) return;
    setQrLoading(true);
    setConnectedStudentName(null);
    setSelectedQrChildId(childId);
    setShowQrModal(true);
    try {
      const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
      const res = await fetch(`${apiBase}/api/v1/auth/qr/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${teacherToken}`,
        },
        body: JSON.stringify({
          child_id: childId,
        }),
      });

      if (!res.ok) throw new Error('Gagal membuat QR token.');

      const data = await res.json();
      setQrToken(data.token);
      setQrStatus(data.status);
    } catch (err) {
      console.error(err);
    } finally {
      setQrLoading(false);
    }
  };

  // Polling Status QR Token
  useEffect(() => {
    if (!qrToken || !teacherToken || qrStatus !== 'pending') return;

    const apiBase = localStorage.getItem('api_base_url') || 'http://localhost:3006';
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${apiBase}/api/v1/auth/qr/status/${qrToken}`, {
          headers: { Authorization: `Bearer ${teacherToken}` },
        });

        if (res.ok) {
          const data = await res.json();
          setQrStatus(data.status);

          if (data.status === 'used') {
            playSuccessSound();
            setConnectedStudentName(data.child_name || 'Siswa');
            setQrToken(null); // stop polling
            fetchChildren(teacherToken); // refresh stats

            setTimeout(() => {
              setShowQrModal(false);
              setConnectedStudentName(null);
            }, 3000);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [qrToken, teacherToken, qrStatus]);

  const playSuccessSound = () => {
    if (typeof window !== 'undefined') {
      try {
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        const playTone = (freq: number, start: number, duration: number) => {
          const osc = audioContext.createOscillator();
          const gain = audioContext.createGain();
          osc.type = 'sine';
          osc.frequency.value = freq;
          gain.gain.setValueAtTime(0, start);
          gain.gain.linearRampToValueAtTime(0.3, start + 0.05);
          gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
          osc.connect(gain);
          gain.connect(audioContext.destination);
          osc.start(start);
          osc.stop(start + duration);
        };
        const now = audioContext.currentTime;
        playTone(523.25, now, 0.2); // C5
        playTone(659.25, now + 0.12, 0.4); // E5
      } catch (e) {}
    }
  };

  const getQRUrl = () => {
    if (typeof window === 'undefined') return '';
    const host = window.location.hostname;
    return `http://${host}:3003/connect?token=${qrToken}&server=http://${host}:3004`;
  };

  // Menghitung Metrik Overview Kelas
  const totalStudents = children.length;
  const highRiskCount = children.filter(c => c.risk_level === 'Tinggi').length;
  const mediumRiskCount = children.filter(c => c.risk_level === 'Sedang').length;
  const lowRiskCount = children.filter(c => c.risk_level === 'Rendah').length;

  return (
    <>
      <div className="background-container">
        <div className="star" style={{ top: '10%', left: '15%', animationDelay: '0.2s' }}></div>
        <div className="star" style={{ top: '60%', left: '80%', animationDelay: '1.5s' }}></div>
        <div className="star" style={{ top: '40%', left: '50%', animationDelay: '2.5s' }}></div>
      </div>

      <div className={styles.container} style={{ maxWidth: '1200px', minHeight: '100vh', padding: '40px 20px' }}>
        <Head>
          <title>DyLeks - Dashboard Guru</title>
        </Head>

        <ThemeToggle />

        {!teacherToken ? (
          // ==================== LAYAR AUTH GURU (LOGIN / REGISTER) ====================
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
            <div style={{ 
              background: theme === 'dark' ? '#181b2a' : '#ffffff', 
              color: theme === 'dark' ? '#ffffff' : '#1a202c', 
              padding: '32px', 
              borderRadius: '24px', 
              width: '100%', 
              maxWidth: '440px', 
              border: theme === 'dark' ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.08)', 
              boxShadow: theme === 'dark' ? '0 20px 25px -5px rgba(0, 0, 0, 0.3)' : '0 10px 30px rgba(0, 0, 0, 0.08)', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '20px', 
              textAlign: 'center',
              position: 'relative'
            }}>

              <div className={styles.mascotContainer} style={{ width: '80px', height: '80px', margin: '0 auto 10px' }}>
                {theme === 'dark' ? <BatMascot /> : <ButterflyMascot />}
              </div>
              <h2 style={{ fontSize: '22px', fontWeight: 'bold', margin: 0 }}>{isRegistering ? 'Daftar Guru Baru' : 'Masuk Dashboard Guru'}</h2>
              <p style={{ fontSize: '13px', color: 'gray', margin: 0 }}>Hubungkan laptop gurumu untuk memantau kemajuan membaca anak luring.</p>

              <form onSubmit={isRegistering ? handleRegister : handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '10px' }}>
                {isRegistering && (
                  <>
                    <input type="text" placeholder="Nama Lengkap" value={fullName} onChange={(e) => setFullName(e.target.value)} required style={{ padding: '12px', borderRadius: '12px', border: '1px solid rgba(128,128,128,0.4)', background: 'transparent', color: 'inherit' }} />
                    <input type="text" placeholder="Nama Sekolah" value={schoolName} onChange={(e) => setSchoolName(e.target.value)} required style={{ padding: '12px', borderRadius: '12px', border: '1px solid rgba(128,128,128,0.4)', background: 'transparent', color: 'inherit' }} />
                    <input type="text" placeholder="Wilayah Sekolah (Contoh: Bandung, Jawa Barat)" value={schoolRegion} onChange={(e) => setSchoolRegion(e.target.value)} required style={{ padding: '12px', borderRadius: '12px', border: '1px solid rgba(128,128,128,0.4)', background: 'transparent', color: 'inherit' }} />
                  </>
                )}
                <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required style={{ padding: '12px', borderRadius: '12px', border: '1px solid rgba(128,128,128,0.4)', background: 'transparent', color: 'inherit' }} />
                <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ padding: '12px', borderRadius: '12px', border: '1px solid rgba(128,128,128,0.4)', background: 'transparent', color: 'inherit' }} />
                
                {authError && <p style={{ color: '#ff4d4d', fontSize: '13px', margin: 0 }}>{authError}</p>}
                
                <button type="submit" style={{ padding: '12px', borderRadius: '12px', background: '#58CC02', color: 'white', fontWeight: 'bold', border: 'none', cursor: 'pointer', marginTop: '10px' }}>
                  {isRegistering ? 'Daftar & Masuk' : 'Masuk'}
                </button>
              </form>

              <p style={{ fontSize: '13px', margin: 0 }}>
                {isRegistering ? 'Sudah punya akun?' : 'Belum punya akun luring?'} {' '}
                <span onClick={() => { setIsRegistering(!isRegistering); setAuthError(null); }} style={{ color: '#58CC02', cursor: 'pointer', textDecoration: 'underline' }}>
                  {isRegistering ? 'Login di sini' : 'Daftar di sini'}
                </span>
              </p>
            </div>
          </div>
        ) : (
          // ==================== UTAMA: DASHBOARD GURU ====================
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px', width: '100%' }}>
            
            {/* Top Navigation Bar */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'flex-start', 
              alignItems: 'center', 
              gap: '12px',
              width: '100%',
              marginBottom: '-10px'
            }}>

              <button 
                onClick={handleLogout} 
                style={{ 
                  padding: '10px 20px', 
                  background: 'linear-gradient(135deg, #e53e3e 0%, #9b2c2c 100%)', 
                  border: 'none', 
                  borderRadius: '12px', 
                  color: 'white', 
                  fontWeight: '600', 
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(229, 62, 62, 0.2)'
                }}
              >
                Logout
              </button>
            </div>

            {/* Header Dashboard */}
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column',
              background: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(255, 255, 255, 0.85)', 
              padding: '24px 30px', 
              borderRadius: '20px', 
              backdropFilter: 'blur(10px)', 
              border: theme === 'dark' ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0, 0, 0, 0.08)',
              boxShadow: theme === 'dark' ? 'none' : '0 10px 30px rgba(0,0,0,0.04)'
            }}>
              <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: theme === 'dark' ? '#ffffff' : '#1a202c', margin: 0 }}>Dashboard Kelas Guru</h1>
              <p style={{ fontSize: '14px', color: theme === 'dark' ? '#a0a0a0' : '#4a5568', margin: '6px 0 0 0' }}>Pantau kemantapan kognitif & tremor motorik anak secara luring.</p>
            </div>

            {/* Overview Stats Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
              <div style={{ 
                background: theme === 'dark' ? 'rgba(255,255,255,0.04)' : '#ffffff', 
                padding: '20px', 
                borderRadius: '20px', 
                border: theme === 'dark' ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0, 0, 0, 0.08)', 
                textAlign: 'center',
                boxShadow: theme === 'dark' ? 'none' : '0 8px 20px rgba(0,0,0,0.02)'
              }}>
                <h3 style={{ fontSize: '14px', color: theme === 'dark' ? 'gray' : '#4a5568', margin: '0 0 8px 0' }}>Total Siswa Terdaftar</h3>
                <p style={{ fontSize: '36px', fontWeight: 'bold', margin: 0, color: '#4299e1' }}>{totalStudents}</p>
              </div>
              <div style={{ 
                background: theme === 'dark' ? 'rgba(229, 62, 62, 0.08)' : '#fff5f5', 
                padding: '20px', 
                borderRadius: '20px', 
                border: theme === 'dark' ? '1px solid rgba(229, 62, 62, 0.2)' : '1px solid rgba(229, 62, 62, 0.25)', 
                textAlign: 'center',
                boxShadow: theme === 'dark' ? 'none' : '0 8px 20px rgba(229, 62, 62, 0.02)'
              }}>
                <h3 style={{ fontSize: '14px', color: theme === 'dark' ? '#feb2b2' : '#c53030', margin: '0 0 8px 0' }}>Risiko Disleksia TINGGI</h3>
                <p style={{ fontSize: '36px', fontWeight: 'bold', margin: 0, color: '#e53e3e' }}>{highRiskCount}</p>
              </div>
              <div style={{ 
                background: theme === 'dark' ? 'rgba(221, 107, 32, 0.08)' : '#fffaf0', 
                padding: '20px', 
                borderRadius: '20px', 
                border: theme === 'dark' ? '1px solid rgba(221, 107, 32, 0.2)' : '1px solid rgba(221, 107, 32, 0.25)', 
                textAlign: 'center',
                boxShadow: theme === 'dark' ? 'none' : '0 8px 20px rgba(221, 107, 32, 0.02)'
              }}>
                <h3 style={{ fontSize: '14px', color: theme === 'dark' ? '#fbd38d' : '#c05621', margin: '0 0 8px 0' }}>Risiko Disleksia SEDANG</h3>
                <p style={{ fontSize: '36px', fontWeight: 'bold', margin: 0, color: '#dd6b20' }}>{mediumRiskCount}</p>
              </div>
              <div style={{ 
                background: theme === 'dark' ? 'rgba(72, 187, 120, 0.08)' : '#f0fff4', 
                padding: '20px', 
                borderRadius: '20px', 
                border: theme === 'dark' ? '1px solid rgba(72, 187, 120, 0.2)' : '1px solid rgba(72, 187, 120, 0.25)', 
                textAlign: 'center',
                boxShadow: theme === 'dark' ? 'none' : '0 8px 20px rgba(72, 187, 120, 0.02)'
              }}>
                <h3 style={{ fontSize: '14px', color: theme === 'dark' ? '#c6f6d5' : '#2f855a', margin: '0 0 8px 0' }}>Risiko Disleksia RENDAH</h3>
                <p style={{ fontSize: '36px', fontWeight: 'bold', margin: 0, color: '#48bb78' }}>{lowRiskCount}</p>
              </div>
            </div>

            {/* Layout Grid: List Siswa + Panel Detail (Side-by-Side jika ada anak yang dipilih) */}
            <div style={{ display: 'grid', gridTemplateColumns: selectedChild ? '2fr 1.3fr' : '1fr', gap: '30px', transition: 'all 0.3s ease' }}>
              
              {/* Box Daftar Siswa */}
              <div style={{ 
                background: theme === 'dark' ? 'rgba(255,255,255,0.05)' : '#ffffff', 
                padding: '30px', 
                borderRadius: '24px', 
                border: theme === 'dark' ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.08)', 
                backdropFilter: 'blur(16px)',
                boxShadow: theme === 'dark' ? 'none' : '0 10px 30px rgba(0,0,0,0.03)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h2 style={{ fontSize: '20px', fontWeight: 'bold', margin: 0, color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>Profil & Status Siswa</h2>
                  <button onClick={() => triggerQrModal(null)} style={{ padding: '10px 18px', background: '#58CC02', color: 'white', border: 'none', borderRadius: '12px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '18px', fontWeight: 'bold' }}>+</span> Tambah Siswa Baru (QR)
                  </button>
                </div>

                {loadingStudents ? (
                  <p style={{ color: 'gray', textAlign: 'center', padding: '40px' }}>Memuat daftar siswa...</p>
                ) : children.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '60px 20px', color: 'gray' }}>
                    <div style={{ fontSize: '48px', marginBottom: '12px' }}>📂</div>
                    <p style={{ margin: 0, color: theme === 'dark' ? 'gray' : '#4a5568' }}>Belum ada profil siswa di bawah pengelolaan Anda.</p>
                    <p style={{ fontSize: '12px', margin: '4px 0 0 0', color: 'gray' }}>Klik tombol "Tambah Profil Siswa" di kanan atas untuk memulai.</p>
                  </div>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ borderBottom: theme === 'dark' ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0, 0, 0, 0.08)', color: theme === 'dark' ? 'gray' : '#4a5568', fontSize: '13px' }}>
                          <th style={{ padding: '12px' }}>Nama</th>
                          <th style={{ padding: '12px' }}>Kelas</th>
                          <th style={{ padding: '12px' }}>Level Saat Ini</th>
                          <th style={{ padding: '12px' }}>Skor Risiko</th>
                          <th style={{ padding: '12px' }}>Tingkat Risiko</th>
                          <th style={{ padding: '12px', textAlign: 'right' }}>Tindakan</th>
                        </tr>
                      </thead>
                      <tbody>
                        {children.map((child) => (
                          <tr
                            key={child.id}
                            style={{
                              borderBottom: theme === 'dark' ? '1px solid rgba(255,255,255,0.05)' : '1px solid rgba(0, 0, 0, 0.06)',
                              cursor: 'pointer',
                              background: selectedChild?.id === child.id ? (theme === 'dark' ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.02)') : 'transparent',
                            }}
                            onClick={() => {
                              setSelectedChild(child);
                              setEditingNotes(child.teacher_notes || '');
                              setActiveTab('profile');
                              if (teacherToken) {
                                fetchPsyRecommendations(child.id, teacherToken);
                                fetchLearningSessions(child.id, teacherToken);
                              }
                            }}
                          >
                            <td style={{ padding: '16px 12px', fontWeight: 'bold', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>{child.name}</td>
                            <td style={{ padding: '16px 12px', color: theme === 'dark' ? '#ffffff' : '#4a5568' }}>{child.grade || '-'}</td>
                            <td style={{ padding: '16px 12px' }}>
                              <span style={{ background: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)', padding: '4px 10px', borderRadius: '8px', fontSize: '12px', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>Level {child.current_level}</span>
                            </td>
                            <td style={{ padding: '16px 12px', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>{child.risk_score.toFixed(1)}%</td>
                            <td style={{ padding: '16px 12px' }}>
                              <span
                                style={{
                                  padding: '4px 10px',
                                  borderRadius: '20px',
                                  fontSize: '11px',
                                  fontWeight: 'bold',
                                  background:
                                    child.risk_level === 'Tinggi'
                                      ? 'rgba(229,62,62,0.15)'
                                      : child.risk_level === 'Sedang'
                                      ? 'rgba(221,107,32,0.15)'
                                      : 'rgba(72,187,120,0.15)',
                                  color:
                                    child.risk_level === 'Tinggi'
                                      ? (theme === 'dark' ? '#fc8181' : '#c53030')
                                      : child.risk_level === 'Sedang'
                                      ? (theme === 'dark' ? '#fbd38d' : '#c05621')
                                      : (theme === 'dark' ? '#68d391' : '#2f855a'),
                                }}
                              >
                                {child.risk_level}
                              </span>
                            </td>
                            <td style={{ padding: '16px 12px', textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                <button
                                  onClick={() => triggerQrModal(child.id)}
                                  style={{ padding: '6px 12px', background: '#3182ce', color: 'white', border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
                                >
                                  Hubungkan (QR)
                                </button>
                                <button
                                  onClick={() => handleDeleteStudent(child.id)}
                                  style={{ padding: '6px 12px', background: '#e53e3e', color: 'white', border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
                                >
                                  Hapus
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Panel Detail & Catatan Guru (Muncul jika ada siswa yang diklik) */}
              {selectedChild && (
                <div style={{ 
                  background: theme === 'dark' ? 'rgba(255,255,255,0.04)' : '#ffffff', 
                  padding: '30px', 
                  borderRadius: '24px', 
                  border: theme === 'dark' ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  gap: '20px', 
                  position: 'relative',
                  boxShadow: theme === 'dark' ? 'none' : '0 10px 30px rgba(0,0,0,0.03)'
                }}>
                  <button onClick={() => setSelectedChild(null)} style={{ position: 'absolute', top: '20px', right: '20px', background: 'transparent', border: 'none', fontSize: '18px', color: theme === 'dark' ? 'gray' : '#4a5568', cursor: 'pointer' }}>✕</button>

                  <h2 style={{ fontSize: '20px', fontWeight: 'bold', borderBottom: theme === 'dark' ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)', paddingBottom: '10px', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>Detail Siswa</h2>
                  
                  <div>
                    <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: theme === 'dark' ? 'gray' : '#718096' }}>Nama Lengkap</p>
                    <p style={{ margin: 0, fontSize: '16px', fontWeight: 'bold', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>{selectedChild.name}</p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: theme === 'dark' ? 'gray' : '#718096' }}>Usia</p>
                      <p style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>{selectedChild.age || '-'} Tahun</p>
                    </div>
                    <div>
                      <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: theme === 'dark' ? 'gray' : '#718096' }}>Jenis Kelamin</p>
                      <p style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>{selectedChild.gender === 'L' ? 'Laki-laki' : 'Perempuan'}</p>
                    </div>
                  </div>

                  <div>
                    <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: theme === 'dark' ? 'gray' : '#718096' }}>Skor Risiko Disleksia Akhir</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
                      <span style={{ fontSize: '22px', fontWeight: 'bold', color: selectedChild.risk_level === 'Tinggi' ? '#fc8181' : selectedChild.risk_level === 'Sedang' ? '#fbd38d' : '#68d391' }}>
                        {selectedChild.risk_score.toFixed(1)}%
                      </span>
                      <span style={{ fontSize: '12px', color: 'gray' }}>({selectedChild.risk_level})</span>
                    </div>
                  </div>

                  {/* Tab Selector */}
                  <div style={{
                    display: 'flex',
                    borderBottom: theme === 'dark' ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)',
                    margin: '10px 0',
                    gap: '16px'
                  }}>
                    <button
                      onClick={() => setActiveTab('profile')}
                      style={{
                        padding: '8px 16px',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'profile' ? '2px solid #58CC02' : '2px solid transparent',
                        color: activeTab === 'profile' ? (theme === 'dark' ? '#ffffff' : '#1a202c') : 'gray',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        outline: 'none'
                      }}
                    >
                      Profil & Catatan
                    </button>
                    <button
                      onClick={() => setActiveTab('exercises')}
                      style={{
                        padding: '8px 16px',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'exercises' ? '2px solid #58CC02' : '2px solid transparent',
                        color: activeTab === 'exercises' ? (theme === 'dark' ? '#ffffff' : '#1a202c') : 'gray',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        outline: 'none'
                      }}
                    >
                      Statistik & Latihan ({learningSessions.length})
                    </button>
                  </div>

                  {activeTab === 'profile' && (
                    <>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', borderTop: theme === 'dark' ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)', paddingTop: '16px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                          <label style={{ fontSize: '13px', fontWeight: 'bold', color: theme === 'dark' ? '#feb2b2' : '#c53030' }}>Catatan Intervensi Pedagogis Guru (Orton-Gillingham):</label>
                          <button
                            onClick={handleGenerateOgRecommendation}
                            disabled={generatingRec}
                            style={{
                              padding: '6px 12px',
                              background: 'rgba(91, 108, 255, 0.12)',
                              border: '1px solid var(--primary)',
                              borderRadius: '10px',
                              color: 'var(--primary)',
                              fontSize: '11px',
                              fontWeight: 'bold',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px',
                              transition: 'all 0.28s ease',
                              outline: 'none'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = 'rgba(91, 108, 255, 0.22)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = 'rgba(91, 108, 255, 0.12)';
                            }}
                          >
                            ✨ {generatingRec ? 'Menganalisis...' : 'Rekomendasikan Rencana Belajar (OG)'}
                          </button>
                        </div>
                        <textarea
                          value={editingNotes}
                          onChange={(e) => setEditingNotes(e.target.value)}
                          placeholder="Masukkan catatan pengajaran khusus, misalnya: 'Siswa sering membalik huruf b dan d. Rekomendasi intervensi taktil menulis di atas pasir kelas luring.'"
                          rows={5}
                          style={{ padding: '12px', borderRadius: '12px', border: theme === 'dark' ? '1px solid rgba(128,128,128,0.4)' : '1px solid #cbd5e0', background: theme === 'dark' ? 'rgba(0,0,0,0.2)' : '#f7fafc', color: 'inherit', fontSize: '13px', lineHeight: '1.5', resize: 'vertical' }}
                        />
                        <button
                          onClick={handleSaveNotes}
                          disabled={notesSaving}
                          style={{ padding: '10px', background: '#58CC02', color: 'white', border: 'none', borderRadius: '12px', fontWeight: 'bold', cursor: 'pointer', marginTop: '6px' }}
                        >
                          {notesSaving ? 'Menyimpan...' : 'Simpan Catatan Aman'}
                        </button>
                      </div>

                      {/* Rekomendasi Medis/Klinis Psikolog */}
                      <div style={{ 
                        borderTop: theme === 'dark' ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)', 
                        paddingTop: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '10px'
                      }}>
                        <label style={{ fontSize: '13px', fontWeight: 'bold', color: '#3182ce', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                          </svg>
                          Rekomendasi Klinis Psikolog Profesional:
                        </label>

                        {loadingPsyRecommendations ? (
                          <p style={{ fontSize: '12px', color: 'gray' }}>Memuat catatan klinis...</p>
                        ) : psyRecommendations.length === 0 ? (
                          <p style={{ fontSize: '12px', color: 'gray', fontStyle: 'italic', margin: '4px 0 0 0' }}>
                            Belum ada rekomendasi klinis/medis untuk siswa ini.
                          </p>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '250px', overflowY: 'auto', paddingRight: '4px' }}>
                            {psyRecommendations.map((rec) => (
                              <div 
                                key={rec.id} 
                                style={{ 
                                  background: theme === 'dark' ? 'rgba(49, 130, 206, 0.08)' : 'rgba(49, 130, 206, 0.04)', 
                                  border: theme === 'dark' ? '1px solid rgba(49, 130, 206, 0.2)' : '1px solid rgba(49, 130, 206, 0.15)', 
                                  borderRadius: '12px', 
                                  padding: '12px',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '6px'
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#3182ce', fontWeight: 'bold' }}>
                                  <span>{rec.psychologist_name}</span>
                                  <span style={{ fontWeight: 'normal', color: 'gray' }}>
                                    {new Date(rec.created_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })}
                                  </span>
                                </div>
                                <div style={{ fontSize: '12px', color: 'inherit', lineHeight: '1.4' }}>
                                  <strong style={{ display: 'block', fontSize: '11px', color: 'gray', marginBottom: '2px' }}>Observasi Klinis:</strong>
                                  {rec.clinical_notes}
                                </div>
                                <div style={{ fontSize: '12px', color: 'inherit', lineHeight: '1.4', borderTop: '1px dashed rgba(49, 130, 206, 0.15)', paddingTop: '6px', marginTop: '2px' }}>
                                  <strong style={{ display: 'block', fontSize: '11px', color: 'gray', marginBottom: '2px' }}>Rencana Terapi / Rujukan:</strong>
                                  {rec.medical_recommendations}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </>
                  )}

                  {activeTab === 'exercises' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {loadingSessions ? (
                        <p style={{ color: 'gray', fontSize: '13px' }}>Memuat riwayat latihan...</p>
                      ) : learningSessions.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '30px 10px', color: 'gray' }}>
                          <p style={{ margin: 0, fontSize: '13px' }}>Belum ada riwayat latihan luring untuk siswa ini.</p>
                          <p style={{ fontSize: '11px', margin: '4px 0 0 0' }}>Data akan terisi otomatis setelah siswa menyinkronkan latihan.</p>
                        </div>
                      ) : (
                        (() => {
                          const getSessionStats = () => {
                            let totalQuestions = 0;
                            let correctQuestions = 0;
                            let reversals = 0;
                            let omissionOrOther = 0;

                            learningSessions.forEach((s) => {
                              s.responses?.forEach((r: any) => {
                                totalQuestions++;
                                if (r.is_correct) {
                                  correctQuestions++;
                                } else {
                                  const t = (r.target || '').toLowerCase().trim();
                                  const a = (r.attempt || '').toLowerCase().trim();
                                  
                                  if (
                                    (t === 'b' && a === 'd') || (t === 'd' && a === 'b') ||
                                    (t === 'p' && a === 'q') || (t === 'q' && a === 'p') ||
                                    (t === 'u' && a === 'n') || (t === 'n' && a === 'u')
                                  ) {
                                    reversals++;
                                  } else {
                                    omissionOrOther++;
                                  }
                                }
                              });
                            });

                            const averageAccuracy = totalQuestions > 0 ? (correctQuestions / totalQuestions) * 100 : 0;
                            
                            let pattern = 'Tidak ada pola kesalahan';
                            if (reversals > 0 || omissionOrOther > 0) {
                              if (reversals >= omissionOrOther) {
                                pattern = 'Inversi Huruf / Spasial (b/d/p/q)';
                              } else {
                                pattern = 'Penghilangan Huruf / Substitusi';
                              }
                            }

                            return {
                              averageAccuracy: averageAccuracy.toFixed(1),
                              totalQuestions,
                              correctQuestions,
                              pattern,
                              reversals,
                              omissionOrOther
                            };
                          };

                          const stats = getSessionStats();

                          return (
                            <>
                              {/* Card Rangkuman Statistik */}
                              <div style={{
                                background: theme === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                                borderRadius: '16px',
                                border: theme === 'dark' ? '1px solid rgba(255,255,255,0.05)' : '1px solid rgba(0,0,0,0.05)',
                                padding: '16px',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '12px'
                              }}>
                                <h3 style={{ fontSize: '14px', fontWeight: 'bold', margin: 0, color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>
                                  Rangkuman Kemajuan Latihan
                                </h3>
                                
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                    <span style={{ fontSize: '11px', color: 'gray' }}>Rata-rata Akurasi</span>
                                    <span style={{
                                      fontSize: '20px',
                                      fontWeight: 'bold',
                                      color: parseFloat(stats.averageAccuracy) >= 80 ? '#48bb78' : parseFloat(stats.averageAccuracy) >= 50 ? '#dd6b20' : '#e53e3e'
                                    }}>
                                      {stats.averageAccuracy}%
                                    </span>
                                  </div>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                    <span style={{ fontSize: '11px', color: 'gray' }}>Pola Salah Terbanyak</span>
                                    <span style={{ fontSize: '13px', fontWeight: 'bold', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>
                                      {stats.pattern}
                                    </span>
                                  </div>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '12px', borderTop: theme === 'dark' ? '1px dashed rgba(255,255,255,0.08)' : '1px dashed rgba(0,0,0,0.08)', paddingTop: '10px' }}>
                                  <div style={{ fontSize: '11px', color: 'gray' }}>
                                    Total Soal: <strong>{stats.totalQuestions}</strong> (Benar: {stats.correctQuestions})
                                  </div>
                                  <div style={{ fontSize: '11px', color: 'gray', textAlign: 'right' }}>
                                    Inversi: {stats.reversals} | Lainnya: {stats.omissionOrOther}
                                  </div>
                                </div>
                              </div>

                              {/* List Sesi Latihan */}
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                <h3 style={{ fontSize: '14px', fontWeight: 'bold', margin: '10px 0 0 0', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>
                                  Riwayat Sesi Belajar Luring
                                </h3>

                                <div style={{
                                  maxHeight: '350px',
                                  overflowY: 'auto',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '12px',
                                  paddingRight: '4px'
                                }}>
                                  {learningSessions.map((session, sIdx) => {
                                    const durationSec = session.end_time 
                                      ? Math.round((new Date(session.end_time).getTime() - new Date(session.start_time).getTime()) / 1000)
                                      : 0;

                                    return (
                                      <div key={session.id} style={{
                                        background: theme === 'dark' ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.01)',
                                        border: theme === 'dark' ? '1px solid rgba(255,255,255,0.04)' : '1px solid rgba(0,0,0,0.04)',
                                        borderRadius: '12px',
                                        padding: '12px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: '8px'
                                      }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                          <span style={{ fontSize: '12px', fontWeight: 'bold', color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>
                                            Sesi #{learningSessions.length - sIdx}
                                          </span>
                                          <span style={{
                                            fontSize: '12px',
                                            fontWeight: 'bold',
                                            color: session.total_score >= 80 ? '#48bb78' : session.total_score >= 50 ? '#dd6b20' : '#e53e3e'
                                          }}>
                                            Skor: {session.total_score.toFixed(0)}%
                                          </span>
                                        </div>

                                        <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'gray' }}>
                                          <span>Tanggal: {new Date(session.start_time).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</span>
                                          {durationSec > 0 && <span>Durasi: {durationSec} detik</span>}
                                        </div>

                                        {/* Detail Responses */}
                                        <div style={{
                                          borderTop: theme === 'dark' ? '1px dashed rgba(255,255,255,0.05)' : '1px dashed rgba(0,0,0,0.05)',
                                          paddingTop: '8px',
                                          marginTop: '4px',
                                          display: 'flex',
                                          flexDirection: 'column',
                                          gap: '4px'
                                        }}>
                                          {session.responses?.map((resp: any, rIdx: number) => (
                                            <div key={resp.id || rIdx} style={{
                                              display: 'flex',
                                              justifyContent: 'space-between',
                                              alignItems: 'center',
                                              fontSize: '11px',
                                              padding: '2px 0'
                                            }}>
                                              <div style={{ display: 'flex', gap: '8px' }}>
                                                <span style={{ color: resp.is_correct ? '#48bb78' : '#e53e3e', fontWeight: 'bold' }}>
                                                  {resp.is_correct ? '✓' : '✗'}
                                                </span>
                                                <span style={{ color: theme === 'dark' ? '#ffffff' : '#1a202c' }}>
                                                  Target: <strong>{resp.target}</strong>
                                                </span>
                                                {!resp.is_correct && (
                                                  <span style={{ color: 'gray' }}>
                                                    (Jawaban: <span style={{ textDecoration: 'line-through' }}>{resp.attempt}</span>)
                                                  </span>
                                                )}
                                              </div>
                                              <span style={{ color: 'gray' }}>
                                                {(resp.response_time_ms / 1000).toFixed(1)}s
                                              </span>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            </>
                          );
                        })()
                      )}
                    </div>
                  )}
                </div>
              )}

            </div>
          </div>
        )}

        {/* Modal: QR Code Connection Polling */}
        {showQrModal && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '20px' }}>
            <div style={{ background: theme === 'dark' ? '#181b2a' : '#ffffff', color: theme === 'dark' ? '#ffffff' : '#1a202c', padding: '32px', borderRadius: '24px', width: '100%', maxWidth: '400px', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px', textAlign: 'center', position: 'relative' }}>
              
              <button onClick={() => setShowQrModal(false)} style={{ position: 'absolute', top: '20px', right: '20px', background: 'transparent', border: 'none', fontSize: '20px', color: 'gray', cursor: 'pointer' }}>✕</button>

              <h2 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0 }}>
                {selectedQrChildId ? 'Hubungkan Perangkat Siswa' : 'Daftar Siswa Baru'}
              </h2>
              <p style={{ fontSize: '12px', color: 'gray', margin: 0 }}>
                {selectedQrChildId 
                  ? 'Scan QR Code di bawah menggunakan smartphone siswa untuk menyambungkan profil belajar.' 
                  : 'Scan QR Code di bawah menggunakan smartphone siswa untuk mendaftar profil siswa baru secara mandiri.'}
              </p>

              {qrLoading ? (
                <div style={{ padding: '40px' }}>Membuat token koneksi luring...</div>
              ) : qrToken ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                  <div style={{ padding: '12px', background: 'white', borderRadius: '16px', border: '4px solid #58CC02' }}>
                    <QRCodeSVG value={getQRUrl()} size={180} />
                  </div>
                  <p style={{ fontSize: '11px', color: 'gray', wordBreak: 'break-all', margin: 0 }}>
                    Alamat luring kelas:<br/>
                    <code style={{ color: '#58CC02' }}>{getQRUrl()}</code>
                  </p>
                </div>
              ) : null}

              {connectedStudentName && (
                <div style={{ padding: '10px 20px', background: 'rgba(88,204,2,0.1)', color: '#58CC02', border: '1px solid rgba(88,204,2,0.2)', borderRadius: '12px', fontWeight: 'bold', width: '100%' }}>
                  🎉 Siswa "{connectedStudentName}" Terhubung!
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </>
  );
}
