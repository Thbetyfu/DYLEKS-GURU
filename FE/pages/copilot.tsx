import { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import styles from '../styles/Copilot.module.css';
import { useTheme } from '../contexts/ThemeContext';
import ThemeToggle from '../components/ThemeToggle';

interface Message {
  role: 'guru' | 'copilot';
  text: string;
  timestamp: string;
}

interface ScreeningContext {
  child_name?: string;
  risk_level?: string;
  recommended_level?: number;
  detected_errors?: string[];
}

const QUICK_PROMPTS = [
  'Anak saya sering membalik huruf b dan d, apa yang harus saya lakukan?',
  'Bagaimana cara melatih anak yang kesulitan mengingat urutan huruf?',
  'Aktivitas apa yang bisa saya lakukan besok di kelas untuk anak disleksia?',
  'Apa tanda-tanda anak perlu dirujuk ke psikolog?',
];

export default function CopilotPage() {
  const router = useRouter();
  const { theme } = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [context, setContext] = useState<ScreeningContext | null>(null);
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setMounted(true);

    // Ambil context hasil skrining jika ada (dari sessionStorage)
    const screeningRaw = sessionStorage.getItem('dyslexia_result');
    const screeningResults = sessionStorage.getItem('dyslexia_screening_results');

    if (screeningRaw) {
      const data = JSON.parse(screeningRaw);
      setContext({
        risk_level: data.risk_level,
        recommended_level: data.recommended_level,
        detected_errors: data.detected_errors || [],
      });
    } else if (screeningResults) {
      const results = JSON.parse(screeningResults);
      const errors = results.flatMap((r: any) => r.result?.detected_errors || []);
      const avgScore = results.reduce((s: number, r: any) => s + (r.result?.risk_score || 0), 0) / (results.length || 1);
      setContext({
        risk_level: avgScore >= 55 ? 'Tinggi' : avgScore >= 30 ? 'Sedang' : 'Rendah',
        detected_errors: errors.slice(0, 5),
      });
    }

    // Pesan sambutan
    setMessages([{
      role: 'copilot',
      text: 'Halo! Saya DyLeks Copilot, asisten pedagogis berbasis metode Orton-Gillingham. Saya siap membantu Anda merancang strategi intervensi yang tepat untuk siswa dengan disleksia. Apa yang ingin Anda konsultasikan?',
      timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
    }]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    const newUserMsg: Message = {
      role: 'guru',
      text: trimmed,
      timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, newUserMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const payload: any = { message: trimmed };
      if (context) {
        payload.context = context;
      }

      const res = await fetch('http://localhost:3006/api/v1/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      setMessages(prev => [...prev, {
        role: 'copilot',
        text: data.reply || 'Copilot tidak merespons. Coba ulangi.',
        timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'copilot',
        text: 'Tidak dapat terhubung ke server. Pastikan backend DyLeks sudah berjalan di port 3004.',
        timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputText);
    }
  };

  if (!mounted) return null;

  return (
    <div className={styles.pageWrapper}>
      <Head>
        <title>DyLeks Copilot — Asisten Guru AI</title>
        <meta name="description" content="Asisten pedagogis AI untuk guru menangani anak disleksia berbasis metode Orton-Gillingham." />
      </Head>

      <div className={styles.bgOrbs} aria-hidden="true">
        <div className={styles.orb1} />
        <div className={styles.orb2} />
        <div className={styles.orb3} />
      </div>

      <div className={styles.themeTogglePos}>
        <ThemeToggle />
      </div>

      {/* Header */}
      <header className={styles.header}>
        <button className={styles.backBtn} onClick={() => router.push('/')} aria-label="Kembali">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M15 18L9 12L15 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <div className={styles.headerInfo}>
          <div className={styles.avatarPulse}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="currentColor" />
            </svg>
          </div>
          <div>
            <h1 className={styles.headerTitle}>DyLeks Copilot</h1>
            <p className={styles.headerSub}>Asisten Pedagogis Orton-Gillingham</p>
          </div>
        </div>
        {context && (
          <div className={styles.contextBadge}>
            <span className={styles.contextDot} />
            <span>Konteks skrining aktif</span>
          </div>
        )}
      </header>

      {/* Context Banner */}
      {context && (
        <div className={styles.contextBanner}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
            <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <span>
            Copilot sudah memuat data skrining siswa
            {context.risk_level && ` — risiko ${context.risk_level}`}
            {context.recommended_level && `, Level ${context.recommended_level}/5`}.
            Rekomendasi akan disesuaikan secara otomatis.
          </span>
        </div>
      )}

      {/* Chat Area */}
      <main className={styles.chatArea}>
        <div className={styles.messageList}>
          {messages.map((msg, idx) => (
            <div key={idx} className={`${styles.messageBubbleWrap} ${msg.role === 'guru' ? styles.bubbleRight : styles.bubbleLeft}`}>
              {msg.role === 'copilot' && (
                <div className={styles.botAvatar}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="currentColor" />
                  </svg>
                </div>
              )}
              <div className={`${styles.bubble} ${msg.role === 'guru' ? styles.bubbleUser : styles.bubbleBot}`}>
                <p className={styles.bubbleText}>{msg.text}</p>
                <span className={styles.bubbleTime}>{msg.timestamp}</span>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className={`${styles.messageBubbleWrap} ${styles.bubbleLeft}`}>
              <div className={styles.botAvatar}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="currentColor" />
                </svg>
              </div>
              <div className={`${styles.bubble} ${styles.bubbleBot} ${styles.typingBubble}`}>
                <div className={styles.typingDots}>
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Prompts */}
        {messages.length <= 1 && (
          <div className={styles.quickPrompts}>
            <p className={styles.quickLabel}>Pertanyaan umum guru:</p>
            <div className={styles.quickGrid}>
              {QUICK_PROMPTS.map((q, i) => (
                <button key={i} className={styles.quickChip} onClick={() => sendMessage(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Input Area */}
      <div className={styles.inputArea}>
        <div className={styles.inputWrapper}>
          <textarea
            ref={inputRef}
            id="copilot-input"
            className={styles.inputBox}
            rows={1}
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ketik pertanyaan Anda ke DyLeks Copilot..."
            disabled={isLoading}
          />
          <button
            id="copilot-send-btn"
            className={`${styles.sendBtn} ${(!inputText.trim() || isLoading) ? styles.sendBtnDisabled : ''}`}
            onClick={() => sendMessage(inputText)}
            disabled={!inputText.trim() || isLoading}
            aria-label="Kirim"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
        <p className={styles.inputHint}>Enter untuk kirim · Shift+Enter untuk baris baru · Respons bisa 10–30 detik</p>
      </div>
    </div>
  );
}
