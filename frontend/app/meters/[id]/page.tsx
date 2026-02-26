import FlowChart from '../../../components/FlowChart';

export default function MeterDetailPage() {
  const points = Array.from({ length: 24 }).map((_, i) => ({
    time: `${i}:00`,
    flow: 2 + Math.sin(i / 3),
    cap: 4
  }));
  return (
    <>
      <h1>Meter Detail</h1>
      <div className="card"><FlowChart title="Flow vs Capacity" points={points} /></div>
      <div className="card"><h3>Anomalies</h3><p>Spike anomalies are marked in production data mode.</p></div>
    </>
  );
}
