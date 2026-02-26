export default function AdminPage() {
  return (
    <div className="card">
      <h1>Admin</h1>
      <p>Manage meter metadata and review ingestion file load history.</p>
      <p>CSV/XLSX ingestion validates ranges, gaps, and dedupes by meter+timestamp.</p>
    </div>
  );
}
