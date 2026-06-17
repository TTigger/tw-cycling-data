import { useEffect, useState } from "react";
import {
  isFavAthlete, toggleFavAthlete, isFavRace, toggleFavRace,
  type FavAthlete, type FavRace,
} from "../lib/favorites";

type Props = { kind: "athlete"; item: FavAthlete } | { kind: "race"; item: FavRace };

export default function FavButton(props: Props) {
  const read = () => (props.kind === "athlete"
    ? isFavAthlete(props.item.id)
    : isFavRace(props.item.rk, props.item.y));
  const [on, setOn] = useState(false);
  useEffect(() => { setOn(read()); /* localStorage only after mount */ }, [props.kind, props.item]);

  function click() {
    if (props.kind === "athlete") toggleFavAthlete(props.item);
    else toggleFavRace(props.item);
    setOn(read());
  }

  return (
    <button onClick={click} aria-pressed={on} aria-label={on ? "已收藏" : "加入我的最愛"}
      className={`rounded-lg border px-3 py-2 text-sm ${
        on ? "border-accent bg-accent/10 text-accent" : "border-border text-muted hover:text-accent"
      }`}>
      {on ? "★ 已收藏" : "☆ 收藏"}
    </button>
  );
}
