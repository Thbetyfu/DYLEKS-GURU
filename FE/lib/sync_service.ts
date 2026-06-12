/**
 * DyLeks Offline Sync Service.
 * Mengelola antrean sesi skrining luring (offline) di sisi klien (LocalStorage)
 * dan menangani sinkronisasi otomatis ketika koneksi kembali terhubung.
 */

export interface OfflineWordAttempt {
  target_letter: string;
  image_base64: string;
}

export interface OfflineSession {
  id: string; // Temporary client-side UUID
  child_id: string | null;
  timestamp: string;
  word_attempts: OfflineWordAttempt[];
  synced: boolean;
  result?: {
    risk_score: number;
    risk_level: string;
    recommended_level: number;
    feedback: string;
  };
}

const STORAGE_KEY = 'dyleks_sync_queue';
const BACKEND_URL = 'http://localhost:3002';

export class SyncService {
  /**
   * Mengambil semua sesi dari antrean lokal.
   */
  static getQueue(): OfflineSession[] {
    if (typeof window === 'undefined') return [];
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    try {
      return JSON.parse(raw);
    } catch (e) {
      console.error('Gagal membaca antrean sinkronisasi:', e);
      return [];
    }
  }

  /**
   * Menyimpan kembali antrean ke LocalStorage.
   */
  static saveQueue(queue: OfflineSession[]): void {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
    } catch (e) {
      console.error('Gagal menulis ke antrean sinkronisasi:', e);
    }
  }

  /**
   * Menambahkan satu sesi skrining luring ke antrean.
   */
  static addSessionToQueue(session: OfflineSession): void {
    const queue = this.getQueue();
    queue.push(session);
    this.saveQueue(queue);
    console.log(`[SyncService] Sesi offline ${session.id} ditambahkan ke antrean.`);
  }

  /**
   * Mengecek apakah ada data di antrean yang belum disinkronkan.
   */
  static hasUnsynced(): boolean {
    return this.getQueue().some(s => !s.synced);
  }

  /**
   * Menghapus semua sesi yang sudah berhasil disinkronkan dari antrean lokal.
   */
  static clearSynced(): void {
    const queue = this.getQueue();
    const unsynced = queue.filter(s => !s.synced);
    this.saveQueue(unsynced);
  }

  /**
   * Melakukan ping ke backend untuk memastikan koneksi aktif.
   */
  static async pingBackend(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 3000); // timeout 3 detik
      
      const res = await fetch(`${BACKEND_URL}/`, {
        method: 'GET',
        signal: controller.signal
      });
      clearTimeout(id);
      return res.ok;
    } catch (e) {
      return false;
    }
  }

  /**
   * Mengirimkan semua data yang belum disinkronkan ke server.
   */
  static async syncQueue(): Promise<{ success: boolean; syncedCount: number }> {
    const queue = this.getQueue();
    const unsynced = queue.filter(s => !s.synced);
    
    if (unsynced.length === 0) {
      return { success: true, syncedCount: 0 };
    }

    // Ping terlebih dahulu untuk memastikan konektivitas
    const online = await this.pingBackend();
    if (!online) {
      console.warn('[SyncService] Sinkronisasi tertunda: backend tidak terjangkau.');
      return { success: false, syncedCount: 0 };
    }

    try {
      // Siapkan payload dengan format sesuai SyncRequest di backend
      const payload = {
        sessions: unsynced.map(s => ({
          id: s.id,
          child_id: s.child_id,
          timestamp: s.timestamp,
          word_attempts: s.word_attempts.map(a => ({
            target_letter: a.target_letter,
            image_base64: a.image_base64
          }))
        }))
      };

      const response = await fetch(`${BACKEND_URL}/api/v1/sync/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Sync HTTP error: ${response.status}`);
      }

      const data = await response.json();
      const syncedResults = data.synced_sessions || [];

      // Perbarui antrean lokal berdasarkan hasil yang dikembalikan server
      const updatedQueue = queue.map(s => {
        const match = syncedResults.find((r: any) => r.client_id === s.id);
        if (match) {
          return {
            ...s,
            synced: true,
            result: {
              risk_score: match.risk_score,
              risk_level: match.risk_level,
              recommended_level: match.recommended_level,
              feedback: match.feedback
            }
          };
        }
        return s;
      });

      this.saveQueue(updatedQueue);
      console.log(`[SyncService] Sukses sinkronisasi ${syncedResults.length} sesi.`);
      return { success: true, syncedCount: syncedResults.length };
    } catch (e) {
      console.error('[SyncService] Gagal memproses sinkronisasi batch:', e);
      return { success: false, syncedCount: 0 };
    }
  }
}
