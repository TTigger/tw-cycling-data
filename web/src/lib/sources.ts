/** Curated human-readable name + link for each scraped source platform. */
export const SOURCE_INFO: Record<string, { name: string; url: string }> = {
  "bravelog.tw": { name: "Bravelog 運動趣", url: "https://www.bravelog.tw/" },
  "irunner.biji.co": { name: "iRunner(biji 運動社群)", url: "https://irunner.biji.co/" },
  "tsu.com.tw": { name: "運動筆記", url: "https://www.tsu.com.tw/" },
  "taiwanbike.org": { name: "中華民國自行車協會(TBA)", url: "https://taiwanbike.org/" },
  "twbike.org": { name: "中華民國登山車協會", url: "https://twbike.org/" },
  "cyclist.org.tw": { name: "自行車騎士協會", url: "https://www.cyclist.org.tw/" },
  "criterium.tw": { name: "criterium.tw(TCU 城市繞圈賽)", url: "https://criterium.tw/" },
  "cycling.org.tw": { name: "中華民國自由車協會", url: "https://cycling.org.tw/" },
};

/** Look up a source domain; unknown -> the domain itself with no link. */
export function sourceInfo(domain: string): { name: string; url: string } {
  return SOURCE_INFO[domain] ?? { name: domain, url: "" };
}
