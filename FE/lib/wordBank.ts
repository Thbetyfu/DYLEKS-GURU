/**
 * DyLeks Word Bank — Sumber Tunggal Kata Per Level.
 *
 * Alasan ('Why'):
 *   Sebelumnya word list tersebar di screening.tsx, latihan.tsx (2 fungsi berbeda),
 *   dan game.tsx. Duplikasi ini menyebabkan inkonsistensi antar modul.
 *   File ini menjadi Single Source of Truth untuk seluruh kurikulum 5-level DyLeks,
 *   mengacu pada prinsip Orton-Gillingham: sistematis, kumulatif, fonetik.
 */

export interface WordItem {
  target: string;
  audio?: string;       // Nama file audio opsional (tanpa path)
  hint?: string;        // Hint visual untuk anak
}

export interface LevelData {
  label: string;
  description: string;
  targets: WordItem[];
  distractors: string[];  // Kata pengecoh untuk quiz mode
}

/** Kurikulum 5-Level DyLeks berbasis Orton-Gillingham */
export const WORD_BANK: Record<number, LevelData> = {
  1: {
    label: 'Level 1',
    description: 'Huruf Vokal Tunggal',
    targets: [
      { target: 'A', hint: 'Huruf pertama dalam alfabet' },
      { target: 'I', hint: 'Bunyi paling tipis' },
      { target: 'U', hint: 'Huruf bibir bulat' },
      { target: 'E', hint: 'Bunyi tengah' },
      { target: 'O', hint: 'Huruf lingkaran' },
    ],
    distractors: [],  // Level 1: pilih dari targets sendiri
  },
  2: {
    label: 'Level 2',
    description: 'Suku Kata Dasar (KV)',
    targets: [
      { target: 'BUKU', hint: 'Tempat menyimpan cerita' },
      { target: 'MAMA', hint: 'Orang tua perempuan' },
      { target: 'IBU',  hint: 'Panggilan ibu' },
      { target: 'BOLA', hint: 'Benda bulat untuk bermain' },
      { target: 'BATU', hint: 'Benda keras dari tanah' },
      { target: 'KAKI', hint: 'Bagian tubuh untuk berjalan' },
      { target: 'MEJA', hint: 'Tempat belajar dan makan' },
      { target: 'SAPI', hint: 'Hewan penghasil susu' },
    ],
    distractors: ['BAKU', 'SAMA', 'PAPA', 'BALA', 'KUKU', 'NANA', 'POLA', 'RATU', 'BATI', 'MAJU'],
  },
  3: {
    label: 'Level 3',
    description: 'Suku Kata Kompleks (KVK)',
    targets: [
      { target: 'BAN',   hint: 'Bagian luar roda kendaraan' },
      { target: 'BUS',   hint: 'Kendaraan umum besar' },
      { target: 'MOBIL', hint: 'Kendaraan bermotor empat roda' },
      { target: 'KAPAL', hint: 'Kendaraan di lautan' },
      { target: 'GELAS', hint: 'Tempat minum' },
      { target: 'BUKU',  hint: 'Tempat menyimpan cerita' },
      { target: 'RUMAH', hint: 'Tempat tinggal' },
      { target: 'PINTU', hint: 'Jalan masuk ke ruangan' },
    ],
    distractors: ['BAK', 'BAS', 'MODEL', 'KAPAS', 'KAPUR', 'KAPAN', 'MODAL', 'GULUS', 'BUKU', 'RUMUT', 'PINDU'],
  },
  4: {
    label: 'Level 4',
    description: 'Fonem Digraf & Diftong',
    targets: [
      { target: 'PISANG',   hint: 'Buah berwarna kuning' },
      { target: 'NYANYI',   hint: 'Mengeluarkan suara lagu' },
      { target: 'KHAWATIR', hint: 'Merasa cemas atau takut' },
      { target: 'SYARAT',   hint: 'Ketentuan yang harus dipenuhi' },
      { target: 'NYAMUK',   hint: 'Serangga penghisap darah' },
      { target: 'NGANGA',   hint: 'Membuka mulut lebar' },
      { target: 'PANTAI',   hint: 'Tepian laut berpasir' },
      { target: 'PULAU',    hint: 'Daratan dikelilingi air' },
    ],
    distractors: ['PISAN', 'NANI', 'KAWATIR', 'SARAT', 'NAMUK', 'PIANG', 'NYALI', 'SAYAT', 'NANGA', 'PANTUI', 'PULAO'],
  },
  5: {
    label: 'Level 5',
    description: 'Kata Morfologi STEM',
    targets: [
      { target: 'MENULIS',   hint: 'Kegiatan membuat tulisan' },
      { target: 'MEMBACA',   hint: 'Kegiatan menyimak tulisan' },
      { target: 'BERMAIN',   hint: 'Kegiatan menyenangkan' },
      { target: 'BERLARI',   hint: 'Bergerak cepat dengan kaki' },
      { target: 'TERJATUH',  hint: 'Jatuh tidak sengaja' },
      { target: 'TERBUKA',   hint: 'Tidak tertutup' },
      { target: 'MEWARNAI',  hint: 'Memberi warna pada gambar' },
      { target: 'AMBILKAN',  hint: 'Tolong ambilkan sesuatu' },
      { target: 'ENERGI',    hint: 'Sumber tenaga (STEM)' },
      { target: 'MAGNET',    hint: 'Benda yang menarik besi (STEM)' },
    ],
    distractors: ['PENULIS', 'PEMBACA', 'MAINAN', 'LARI', 'JATUH', 'BUKA', 'WARNA', 'AMBIL', 'ENERGIK', 'MAGNETIK'],
  },
};

/** Kata-kata skrining yang diurutkan dari mudah ke sulit (5 level) */
export const SCREENING_WORDS: string[] = ['A', 'BA', 'BAN', 'NYALA', 'MENEMANI'];

/**
 * Mengambil target acak dari level tertentu (menghindari pengulangan langsung)
 */
export function getRandomTarget(level: number, exclude?: string): WordItem {
  const data = WORD_BANK[level] || WORD_BANK[1];
  const pool = exclude
    ? data.targets.filter(w => w.target !== exclude)
    : data.targets;
  return pool[Math.floor(Math.random() * pool.length)];
}

/**
 * Menghasilkan opsi quiz: 1 jawaban benar + 3 pengecoh acak
 */
export function buildQuizOptions(level: number, target: string): string[] {
  const data = WORD_BANK[level] || WORD_BANK[1];

  if (level === 1) {
    // Level 1: semua vokal sebagai opsi
    return data.targets.map(w => w.target);
  }

  const distractorPool = [
    ...data.distractors,
    ...data.targets.filter(w => w.target !== target).map(w => w.target),
  ];

  const shuffled = distractorPool
    .filter(w => w.toUpperCase() !== target.toUpperCase())
    .sort(() => Math.random() - 0.5)
    .slice(0, 3);

  return [target, ...shuffled].sort(() => Math.random() - 0.5);
}
