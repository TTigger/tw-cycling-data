export default function VamMethodology() {
  return (
    <div className="space-y-1 text-xs text-muted">
      <p><b className="text-ink">VAM</b>(Vertical Ascent Metres/hour)= 總爬升公尺 ÷ 完賽時數,衡量純爬升速度,跨年跨賽可比。</p>
      <p><b className="text-ink">推算 W/kg</b> 用 Ferrari 公式 <span className="num">VAM /(100·(2+均斜率%/10))</span> 估計相對功率——<b>非實測</b>,無體重/功率計,僅供參考;低均斜率路線(如含長緩坡的 KOM)估值較不準。</p>
      <p>各爬坡賽的距離/爬升見排行榜標頭;標「估計」者路線數據為估算。VAM 僅取 100–3000 之間(濾除計時錯誤/未完賽)。</p>
    </div>
  );
}
