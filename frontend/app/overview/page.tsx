export default function OverviewPage() {
  return (
    <>
      <h1>Overview Dashboard</h1>
      <div className="grid">
        <div className="card"><h3>System Utilization</h3><p>74%</p></div>
        <div className="card"><h3>Exceedances (24h)</h3><p>8 events</p></div>
        <div className="card"><h3>Hotspot Basins</h3><p>Basin 1, Basin 3</p></div>
      </div>
      <div className="card"><h3>Storm Spikes</h3><p>Rainfall overlay appears when rainfall exists.</p></div>
    </>
  );
}
