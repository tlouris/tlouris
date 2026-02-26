export default function ComparisonPage() {
  return (
    <div className="card">
      <h1>Trend Comparison</h1>
      <p>Compare one meter across periods or multiple meters in the same date range.</p>
      <ul>
        <li>This month vs last month vs same month last year</li>
        <li>Top N meters by peak utilization and exceedance duration</li>
        <li>Basin-level rollups and hotspots</li>
      </ul>
    </div>
  );
}
