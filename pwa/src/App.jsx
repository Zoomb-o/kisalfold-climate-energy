import { useState, useEffect } from "react"
import Papa from "papaparse"
import {
  LineChart, Line, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine
} from "recharts"

// ── Theme ─────────────────────────────────────────────────────────────────
const COLORS = {
  ssp126: "#1A85FF",
  ssp245: "#FFA500",
  ssp585: "#D41159",
  observed: "#222222",
  accent: "#2D6A4F",
  warm: "#E76F51",
}

const SCENARIO_LABELS = {
  "SSP1-2.6": "SSP1-2.6 — Optimistic (≈1.5°C)",
  "SSP2-4.5": "SSP2-4.5 — Moderate (≈2°C)",
  "SSP5-8.5": "SSP5-8.5 — High emissions (≈3°C+)",
}

const scenarioColor = {
  "SSP1-2.6": COLORS.ssp126,
  "SSP2-4.5": COLORS.ssp245,
  "SSP5-8.5": COLORS.ssp585,
}

// ── CSV loader ────────────────────────────────────────────────────────────
const BASE = import.meta.env.BASE_URL

function loadCSV(path) {
  return new Promise((resolve) => {
    Papa.parse(BASE + path, {
      download: true,
      header: true,
      dynamicTyping: true,
      complete: (r) => resolve(r.data.filter(d => d && Object.keys(d).length > 1)),
    })
  })
}

// ── Shared components ─────────────────────────────────────────────────────
function Card({ children, style }) {
  return (
    <div style={{
      background: "white",
      borderRadius: 20,
      padding: "2rem",
      boxShadow: "0 2px 20px rgba(0,0,0,0.07)",
      marginBottom: "2rem",
      ...style,
    }}>
      {children}
    </div>
  )
}

function SectionTitle({ number, title, subtitle }) {
  return (
    <div style={{ marginBottom: "2rem", textAlign: "center" }}>
      <div style={{
        display: "inline-block",
        background: "#2D6A4F",
        color: "white",
        borderRadius: 99,
        padding: "0.2rem 0.8rem",
        fontSize: "0.75rem",
        fontWeight: 700,
        letterSpacing: "0.08em",
        marginBottom: "0.6rem",
        fontFamily: "system-ui",
      }}>
        {number}
      </div>
      <h2 style={{
        fontSize: "clamp(1.4rem, 3vw, 2rem)",
        fontWeight: 800,
        margin: "0 0 0.4rem",
        color: "#1a1a1a",
      }}>
        {title}
      </h2>
      {subtitle && (
        <p style={{
          color: "#666",
          fontSize: "1rem",
          margin: "0 auto",
          maxWidth: 600,
          lineHeight: 1.6,
        }}>
          {subtitle}
        </p>
      )}
    </div>
  )
}

function StatCard({ value, unit, label, sub, color }) {
  return (
    <div style={{
      background: "white",
      borderRadius: 16,
      padding: "1.5rem",
      boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
      borderTop: `4px solid ${color}`,
      flex: 1,
      minWidth: 180,
      textAlign: "center",
    }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 4, justifyContent: "center" }}>
        <span style={{ fontSize: "2rem", fontWeight: 800, color, lineHeight: 1 }}>{value}</span>
        {unit && <span style={{ fontSize: "0.95rem", fontWeight: 700, color }}>{unit}</span>}
      </div>
      <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "#333", marginTop: 6 }}>{label}</div>
      {sub && <div style={{ fontSize: "0.8rem", color: "#888", marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function Glossary() {
  const terms = [
    { term: "HDD", full: "Heating Degree Days", desc: "A measure of how cold it is — how much energy is needed to heat buildings. Higher = colder winter." },
    { term: "CDD", full: "Cooling Degree Days", desc: "A measure of how hot it is — how much energy is needed to cool buildings. Higher = hotter summer." },
    { term: "SSP1-2.6", full: "Optimistic scenario", desc: "Strong climate action. Global warming stays near 1.5°C. Emissions fall sharply after 2025." },
    { term: "SSP2-4.5", full: "Moderate scenario", desc: "Some climate action. Warming reaches ~2°C by 2100. Current policies roughly maintained." },
    { term: "SSP5-8.5", full: "High emissions scenario", desc: "Little climate action. Warming exceeds 3°C by 2100. Fossil fuel use continues to grow." },
    { term: "ERA5", full: "Climate reanalysis dataset", desc: "54 years of reconstructed weather data from the Copernicus Climate programme. Our historical baseline." },
  ]
  return (
    <Card style={{ background: "#FFFBF5" }}>
      <SectionTitle
        number="GLOSSARY"
        title="Key terms explained"
        subtitle="Not familiar with climate science jargon? Here's what the terms in this study mean."
      />
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
        gap: "1rem",
      }}>
        {terms.map(t => (
          <div key={t.term} style={{
            background: "white",
            borderRadius: 12,
            padding: "1rem 1.25rem",
            boxShadow: "0 1px 6px rgba(0,0,0,0.06)",
          }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 4 }}>
              <span style={{
                fontFamily: "system-ui",
                fontWeight: 800,
                fontSize: "1rem",
                color: "#2D6A4F",
              }}>{t.term}</span>
              <span style={{
                fontFamily: "system-ui",
                fontSize: "0.75rem",
                color: "#888",
                fontWeight: 500,
              }}>{t.full}</span>
            </div>
            <p style={{
              fontFamily: "system-ui",
              fontSize: "0.85rem",
              color: "#555",
              margin: 0,
              lineHeight: 1.5,
            }}>{t.desc}</p>
          </div>
        ))}
      </div>
    </Card>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────
export default function App() {
  const [era5, setEra5] = useState([])
  const [master, setMaster] = useState([])
  const [projections, setProjections] = useState([])
  const [demandProj, setDemandProj] = useState([])
  const [scenario, setScenario] = useState("SSP2-4.5")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      loadCSV("data/era5_daily.csv"),
      loadCSV("data/master_dataset.csv"),
      loadCSV("data/cmip6_projections.csv"),
      loadCSV("data/demand_projections.csv"),
    ]).then(([e, m, p, d]) => {
      setEra5(e)
      setMaster(m)
      setProjections(p)
      setDemandProj(d)
      setLoading(false)
    })
  }, [])

  // Annual ERA5 aggregation
  const era5Annual = Object.values(
    era5.reduce((acc, row) => {
      const y = row.date?.slice(0, 4)
      if (!y) return acc
      if (!acc[y]) acc[y] = { year: +y, temps: [], HDD: 0, CDD: 0 }
      acc[y].temps.push(row.temp_mean_c)
      acc[y].HDD += row.HDD || 0
      acc[y].CDD += row.CDD || 0
      return acc
    }, {})
  ).map(d => ({
    ...d,
    temp: d.temps.reduce((a, b) => a + b, 0) / d.temps.length,
  }))
  .filter(d => d.year >= 1970 && d.year <= 2024)
  .sort((a, b) => a.year - b.year)

  // Projections for selected scenario
  const scenarioProj = projections
    .filter(d => d.scenario === scenario)
    .reduce((acc, row) => {
      if (!acc[row.year]) acc[row.year] = { year: row.year, HDD: 0, CDD: 0, temps: [] }
      acc[row.year].temps.push(row.temp_mean_c)
      acc[row.year].HDD += row.HDD_monthly || 0
      acc[row.year].CDD += row.CDD_monthly || 0
      return acc
    }, {})

  const scenarioProjAnnual = Object.values(scenarioProj)
    .map(d => ({
      ...d,
      temp: d.temps.reduce((a, b) => a + b, 0) / d.temps.length,
    }))
    .sort((a, b) => a.year - b.year)

  // Demand projections grouped by scenario
  const demandByScenario = {}
  demandProj.forEach(d => {
    if (!demandByScenario[d.scenario]) demandByScenario[d.scenario] = []
    demandByScenario[d.scenario].push(d)
  })

  // Monthly scatter for temp vs load
  const monthlyScatter = Object.values(
    master.reduce((acc, row) => {
      const key = row.date?.slice(0, 7)
      if (!key) return acc
      if (!acc[key]) acc[key] = { temps: [], loads: [] }
      acc[key].temps.push(row.temp_mean_c)
      acc[key].loads.push(row.load_mean_MW)
      return acc
    }, {})
  ).map(d => ({
    temp: d.temps.reduce((a, b) => a + b, 0) / d.temps.length,
    load: d.loads.reduce((a, b) => a + b, 0) / d.loads.length,
  })).filter(d => d.temp && d.load)

  // 2050 callout values
  const r2050 = scenarioProjAnnual.find(d => d.year === 2050)
  const base2025 = scenarioProjAnnual.find(d => d.year === 2025)
  const hddChange = r2050 && base2025 ? Math.round(r2050.HDD - base2025.HDD) : null
  const cddChange = r2050 && base2025 ? Math.round(r2050.CDD - base2025.CDD) : null

  if (loading) return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#F7F5F0",
      fontFamily: "Georgia, serif",
      fontSize: "1.2rem",
      color: "#666",
    }}>
      Loading climate data...
    </div>
  )

  return (
    <div style={{ fontFamily: "'Georgia', serif", background: "#F7F5F0", minHeight: "100vh" }}>

      {/* ── Hero ── */}
      <div style={{
        background: "linear-gradient(135deg, #1B4332 0%, #2D6A4F 60%, #40916C 100%)",
        color: "white",
        padding: "5rem 2rem 4rem",
        textAlign: "center",
      }}>
        <div style={{
          display: "inline-block",
          background: "rgba(255,255,255,0.15)",
          borderRadius: 99,
          padding: "0.3rem 1rem",
          fontSize: "0.8rem",
          letterSpacing: "0.12em",
          fontWeight: 600,
          marginBottom: "1.5rem",
          fontFamily: "system-ui",
        }}>
          KISALFÖLD · HUNGARY · CLIMATE RESEARCH
        </div>
        <h1 style={{
          fontSize: "clamp(1.8rem, 5vw, 3.5rem)",
          fontWeight: 900,
          margin: "0 0 1rem",
          lineHeight: 1.15,
          maxWidth: 800,
          marginInline: "auto",
        }}>
          How Climate Change Is Reshaping Hungary's Energy Future
        </h1>
        <p style={{
          fontSize: "clamp(1rem, 2vw, 1.25rem)",
          opacity: 0.85,
          maxWidth: 620,
          marginInline: "auto",
          lineHeight: 1.6,
          fontFamily: "system-ui",
        }}>
          A data-driven study of 54 years of climate records, electricity demand,
          and what warming temperatures mean for Hungary's energy infrastructure through 2100.
        </p>
        <div style={{
          display: "flex",
          gap: "1rem",
          justifyContent: "center",
          marginTop: "2.5rem",
          flexWrap: "wrap",
        }}>
          <a href="#explore" style={{
            background: "white",
            color: "#1B4332",
            padding: "0.8rem 2rem",
            borderRadius: 99,
            fontWeight: 700,
            textDecoration: "none",
            fontSize: "0.95rem",
            fontFamily: "system-ui",
          }}>
            Explore the Data ↓
          </a>
          <a href="https://github.com/Zoomb-o/kisalfold-climate-energy"
            target="_blank" rel="noopener"
            style={{
              background: "rgba(255,255,255,0.15)",
              color: "white",
              padding: "0.8rem 2rem",
              borderRadius: 99,
              fontWeight: 700,
              textDecoration: "none",
              fontSize: "0.95rem",
              fontFamily: "system-ui",
              border: "1px solid rgba(255,255,255,0.3)",
            }}>
            View on GitHub →
          </a>
        </div>
      </div>

      {/* ── Key findings ── */}
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "3rem 1.5rem 0" }}>
        <p style={{
          textAlign: "center",
          color: "#666",
          fontSize: "0.8rem",
          letterSpacing: "0.1em",
          fontFamily: "system-ui",
          fontWeight: 600,
          marginBottom: "1rem",
        }}>KEY FINDINGS</p>
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <StatCard value="+0.42" unit="°C" label="Warming per decade" sub="Since 1970, ERA5 reanalysis" color={COLORS.warm} />
          <StatCard value="−92" unit=" HDD" label="Heating days lost per decade" sub="Winters are getting milder" color={COLORS.ssp126} />
          <StatCard value="+48" unit=" CDD" label="Cooling days gained per decade" sub="Summers are getting hotter" color={COLORS.ssp585} />
          <StatCard value="3×" unit="" label="Increase in cooling demand" sub="From 1970 to 2024" color="#9B2226" />
        </div>
      </div>

      {/* ── Main content ── */}
      <div id="explore" style={{ maxWidth: 1100, margin: "0 auto", padding: "3rem 1.5rem" }}>

        {/* Section 1 — Historical warming */}
        <Card>
          <SectionTitle
            number="01 — HISTORICAL CLIMATE"
            title="Kisalföld has warmed by 2.3°C since 1970"
            subtitle="54 years of ERA5 reanalysis data reveal a clear and accelerating warming trend across the Little Hungarian Plain."
          />
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={era5Annual} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis domain={[9, 14]} unit="°C" tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [`${v?.toFixed(2)}°C`, "Mean temperature"]} />
              <ReferenceLine y={10.5} stroke="#ccc" strokeDasharray="4 4"
                label={{ value: "1970s avg", fontSize: 10, fill: "#aaa" }} />
              <Line type="monotone" dataKey="temp" stroke={COLORS.warm}
                dot={{ r: 3, fill: COLORS.warm }} strokeWidth={2}
                name="Annual mean temperature" />
            </LineChart>
          </ResponsiveContainer>
          <div style={{
            display: "flex", gap: "2rem", marginTop: "1.5rem",
            flexWrap: "wrap", fontFamily: "system-ui",
            justifyContent: "center",
          }}>
            {[
              { label: "Heating days lost", value: "−500", unit: "HDD", desc: "since 1970", color: COLORS.ssp126 },
              { label: "Cooling days gained", value: "+250", unit: "CDD", desc: "since 1970", color: COLORS.ssp585 },
              { label: "Hottest year on record", value: "2024", unit: "", desc: "13.1°C annual mean", color: COLORS.warm },
            ].map(item => (
              <div key={item.label} style={{ flex: 1, minWidth: 140, textAlign: "center" }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 4, justifyContent: "center" }}>
                  <span style={{ fontSize: "1.8rem", fontWeight: 800, color: item.color, lineHeight: 1 }}>{item.value}</span>
                  {item.unit && <span style={{ fontSize: "0.9rem", fontWeight: 700, color: item.color }}>{item.unit}</span>}
                </div>
                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#333", marginTop: 4 }}>{item.label}</div>
                <div style={{ fontSize: "0.75rem", color: "#888" }}>{item.desc}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* Section 2 — Temperature vs demand */}
        <Card>
          <SectionTitle
            number="02 — TEMPERATURE & DEMAND"
            title="Demand follows a U-curve: high in cold winters, rising in hot summers"
            subtitle="Monthly electricity load plotted against temperature reveals the classic dual-peak pattern — minimum demand around 17°C."
          />
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart margin={{ top: 5, right: 20, bottom: 30, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="temp" name="Temperature" unit="°C"
                label={{ value: "Monthly mean temperature (°C)", position: "insideBottom", offset: -15, fontSize: 12 }}
                tick={{ fontSize: 11 }} />
              <YAxis dataKey="load" name="Load" unit=" MW" tick={{ fontSize: 11 }} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }}
                formatter={(v, n) => n === "Temperature"
                  ? [`${v?.toFixed(1)}°C`, n]
                  : [`${v?.toFixed(0)} MW`, n]} />
              <Scatter data={monthlyScatter} fill={COLORS.accent} opacity={0.6} r={4} />
            </ScatterChart>
          </ResponsiveContainer>
          <p style={{
            fontFamily: "system-ui", fontSize: "0.9rem", color: "#666",
            marginTop: "1rem", background: "#F0F7F4", borderRadius: 10,
            padding: "0.8rem 1rem", borderLeft: "3px solid #2D6A4F",
          }}>
            💡 <strong>What this means:</strong> As climate change pushes temperatures higher,
            summer cooling demand will increasingly dominate — shifting Hungary's grid from
            a winter-peak to a summer-peak system for the first time.
          </p>
        </Card>

        {/* Section 3 — Scenario explorer */}
        <Card>
          <SectionTitle
            number="03 — FUTURE SCENARIOS"
            title="Explore projections under different warming pathways"
            subtitle="Select a climate scenario to see how temperature, heating demand, and cooling demand evolve to 2100."
          />

          <div style={{ display: "flex", gap: "0.75rem", marginBottom: "2rem", flexWrap: "wrap", justifyContent: "center" }}>
            {Object.entries(SCENARIO_LABELS).map(([key, label]) => (
              <button key={key} onClick={() => setScenario(key)}
                style={{
                  padding: "0.6rem 1.2rem", borderRadius: 99,
                  border: `2px solid ${scenarioColor[key]}`,
                  background: scenario === key ? scenarioColor[key] : "transparent",
                  color: scenario === key ? "white" : scenarioColor[key],
                  fontWeight: 700, cursor: "pointer",
                  fontSize: "0.85rem", fontFamily: "system-ui",
                  transition: "all 0.2s",
                }}>
                {key}
              </button>
            ))}
          </div>

          <div style={{
            background: "#F7F5F0", borderRadius: 12,
            padding: "1rem 1.25rem", marginBottom: "1.5rem",
            fontFamily: "system-ui", fontSize: "0.9rem", color: "#444",
            borderLeft: `4px solid ${scenarioColor[scenario]}`,
            textAlign: "center",
          }}>
            <strong>{scenario}:</strong> {SCENARIO_LABELS[scenario].split("—")[1]}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            <div>
              <p style={{ fontFamily: "system-ui", fontSize: "0.85rem", fontWeight: 600, color: "#666", margin: "0 0 0.5rem", textAlign: "center" }}>
                HEATING DEGREE DAYS (HDD) — less heating needed over time
              </p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} type="number" domain={[1970, 2100]} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <ReferenceLine x={2024} stroke="#ccc" strokeDasharray="4 4" />
                  <Line data={era5Annual} type="monotone" dataKey="HDD"
                    stroke={COLORS.observed} strokeWidth={1.5} dot={false} name="Observed (ERA5)" />
                  <Line data={scenarioProjAnnual} type="monotone" dataKey="HDD"
                    stroke={scenarioColor[scenario]} strokeWidth={2}
                    dot={false} name={scenario} strokeDasharray="6 3" />
                  <Legend />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div>
              <p style={{ fontFamily: "system-ui", fontSize: "0.85rem", fontWeight: 600, color: "#666", margin: "0 0 0.5rem", textAlign: "center" }}>
                COOLING DEGREE DAYS (CDD) — more cooling needed over time
              </p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} type="number" domain={[1970, 2100]} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <ReferenceLine x={2024} stroke="#ccc" strokeDasharray="4 4" />
                  <Line data={era5Annual} type="monotone" dataKey="CDD"
                    stroke={COLORS.observed} strokeWidth={1.5} dot={false} name="Observed (ERA5)" />
                  <Line data={scenarioProjAnnual} type="monotone" dataKey="CDD"
                    stroke={scenarioColor[scenario]} strokeWidth={2}
                    dot={false} name={scenario} strokeDasharray="6 3" />
                  <Legend />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {hddChange !== null && cddChange !== null && (
            <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem", flexWrap: "wrap", fontFamily: "system-ui" }}>
              <div style={{ flex: 1, background: "#EBF5FB", borderRadius: 12, padding: "1rem", textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 800, color: COLORS.ssp126 }}>
                  {hddChange > 0 ? "+" : ""}{hddChange}
                </div>
                <div style={{ fontSize: "0.8rem", color: "#555" }}>Heating days change by 2050</div>
              </div>
              <div style={{ flex: 1, background: "#FEF0F0", borderRadius: 12, padding: "1rem", textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 800, color: COLORS.ssp585 }}>
                  +{cddChange}
                </div>
                <div style={{ fontSize: "0.8rem", color: "#555" }}>Cooling days gained by 2050</div>
              </div>
              <div style={{ flex: 1, background: "#F0F7F4", borderRadius: 12, padding: "1rem", textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 800, color: COLORS.accent }}>
                  {r2050?.temp?.toFixed(1)}°C
                </div>
                <div style={{ fontSize: "0.8rem", color: "#555" }}>Projected mean temperature 2050</div>
              </div>
            </div>
          )}
        </Card>

        {/* Section 4 — Transmission losses */}
        <Card>
          <SectionTitle
            number="04 — THE HIDDEN COST"
            title="Hotter temperatures waste more electricity before it reaches homes"
            subtitle="Electrical resistance in power lines increases with heat. On the hottest days — when demand is highest — more energy is lost in transmission."
          />
          <ResponsiveContainer width="100%" height={280}>
            <LineChart margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} type="number"
                domain={[2025, 2100]} allowDuplicatedCategory={false} />
              <YAxis tick={{ fontSize: 11 }} unit=" MW" />
              <Tooltip formatter={(v) => [`${v?.toFixed(0)} MW`, "Energy wasted"]} />
              <Legend />
              <ReferenceLine x={2050} stroke="#ccc" strokeDasharray="4 4"
                label={{ value: "2050", fontSize: 10, fill: "#aaa" }} />
              {Object.entries(demandByScenario).map(([sc, data]) => (
                <Line key={sc} data={data} type="monotone" dataKey="wasted_MW"
                  stroke={scenarioColor[sc]} strokeWidth={2}
                  dot={false} name={sc} />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <p style={{
            fontFamily: "system-ui", fontSize: "0.9rem", color: "#666",
            marginTop: "1rem", background: "#FFF8F0", borderRadius: 10,
            padding: "0.8rem 1rem", borderLeft: "3px solid #E76F51",
          }}>
            ⚡ <strong>Under the high-emissions scenario</strong>, Hungary's grid could be
            wasting an additional ~90 MW continuously by 2100 compared to today —
            equivalent to powering a city of 50,000 homes, lost purely to heat.
          </p>
        </Card>

        {/* Glossary */}
        <Glossary />

        {/* Section 5 — About */}
        <Card style={{ background: "#1B4332", color: "white" }}>
          <SectionTitle
            number="05 — ABOUT THIS STUDY"
            title="Open science, open data"
            subtitle=""
          />
          <p style={{
            fontFamily: "system-ui", fontSize: "0.95rem",
            lineHeight: 1.7, color: "rgba(255,255,255,0.8)",
            maxWidth: 650, margin: "0 auto 1.5rem", textAlign: "center",
          }}>
            This study combines 54 years of ERA5 climate reanalysis, 16 years of
            upper-air sounding data from WMO station 12843, and 10 years of Hungarian
            national grid load data from ENTSO-E. Future projections use IPCC AR6
            warming scenarios for Central Europe. An XGBoost machine learning model
            (R²=0.77) links climate variables to electricity demand.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            {[
              { label: "GitHub Repository", href: "https://github.com/Zoomb-o/kisalfold-climate-energy" },
              { label: "ERA5 Data (Copernicus)", href: "https://cds.climate.copernicus.eu" },
              { label: "ENTSO-E Transparency", href: "https://transparency.entsoe.eu" },
            ].map(link => (
              <a key={link.label} href={link.href} target="_blank" rel="noopener"
                style={{
                  background: "rgba(255,255,255,0.12)",
                  color: "white", padding: "0.6rem 1.2rem",
                  borderRadius: 99, textDecoration: "none",
                  fontSize: "0.85rem", fontFamily: "system-ui",
                  fontWeight: 600, border: "1px solid rgba(255,255,255,0.2)",
                }}>
                {link.label} →
              </a>
            ))}
          </div>
          <p style={{
            fontFamily: "system-ui", fontSize: "0.8rem",
            color: "rgba(255,255,255,0.4)", marginTop: "2rem",
            textAlign: "center",
          }}>
            Pápa, Kisalföld, Hungary · Data: ERA5, ENTSO-E, IPCC AR6 · Code: MIT License
          </p>
        </Card>

      </div>
    </div>
  )
}