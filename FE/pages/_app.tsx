import type { AppProps } from 'next/app';
import { Lexend } from 'next/font/google';
import '../styles/globals.css';
import { ThemeProvider } from '../contexts/ThemeContext';
import ConnectivityAlert from '../components/ConnectivityAlert';

/*
 * Lexend dipilih karena dirancang secara klinis oleh Thomas Jockin
 * bersama Google.org untuk meningkatkan readability bagi pembaca
 * dengan disleksia. Studi klinis menunjukkan peningkatan reading speed
 * signifikan dibanding sans-serif generik.
 */
const lexend = Lexend({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-lexend',
  display: 'swap',
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <main className={lexend.className}>
        <ConnectivityAlert />
        <Component {...pageProps} />
      </main>
    </ThemeProvider>
  );
}
