import './styles.css';
import Link from 'next/link';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="nav">
          <Link href="/overview">Overview</Link>
          <Link href="/comparison">Comparison</Link>
          <Link href="/alerts">Alerts</Link>
          <Link href="/admin">Admin</Link>
        </nav>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
