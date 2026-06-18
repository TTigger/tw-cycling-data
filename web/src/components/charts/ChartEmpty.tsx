/** Consistent placeholder shown in place of a chart when there is nothing to
 * plot (no data, or not enough for the view). Pass the chart's normal height so
 * swapping the chart in/out doesn't shift layout. */
export default function ChartEmpty({ children, height = 260 }:
  { children: React.ReactNode; height?: number }) {
  return (
    <div className="flex items-center justify-center px-4 text-center text-sm text-muted"
      style={{ height }}>
      {children}
    </div>
  );
}
