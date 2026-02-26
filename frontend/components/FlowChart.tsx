'use client';
import ReactECharts from 'echarts-for-react';

export default function FlowChart({ title, points }: { title: string; points: { time: string; flow: number; cap: number }[] }) {
  return (
    <ReactECharts
      style={{ height: 320 }}
      option={{
        title: { text: title },
        tooltip: { trigger: 'axis' },
        legend: { data: ['Flow', 'Capacity'] },
        xAxis: { type: 'category', data: points.map((p) => p.time) },
        yAxis: { type: 'value', name: 'MGD' },
        series: [
          { name: 'Flow', type: 'line', data: points.map((p) => p.flow), smooth: true },
          { name: 'Capacity', type: 'line', data: points.map((p) => p.cap), lineStyle: { type: 'dashed' } }
        ]
      }}
    />
  );
}
