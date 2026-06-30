import FinishTimeBand from "../charts/FinishTimeBand";
import type { CrossYearPoint } from "../../lib/overview";

export default function CrossYearTrend({ cy }: { cy: CrossYearPoint[] }) {
  return <FinishTimeBand cy={cy} />;
}
