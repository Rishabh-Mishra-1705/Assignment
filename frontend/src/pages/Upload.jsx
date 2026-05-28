import { useState } from 'react';
import { uploadSAP, uploadUtility, uploadTravel } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const SOURCES = [
  {
    key: 'sap',
    label: 'SAP Fuel & Procurement',
    icon: '⛽',
    scope: 'Scope 1',
    fn: uploadSAP,
    hint: 'CSV with columns: MaterialCode/Materialnummer, Quantity/Menge, Unit/Einheit, PostingDate/Buchungsdatum',
    sampleRows:
      'MaterialCode,PlantCode,Quantity,Unit,PostingDate,DocumentNumber,Cost,Currency\nDIESEL,DE01,500,L,20231015,INV-001,850,EUR\nNATGAS,DE02,1200,KG,20231020,INV-002,960,EUR',
  },
  {
    key: 'utility',
    label: 'Utility Electricity',
    icon: '⚡',
    scope: 'Scope 2',
    fn: uploadUtility,
    hint: 'CSV with columns: MeterID, ConsumptionKWh/Quantity, Unit, BillingEnd, Cost, Currency',
    sampleRows:
      'MeterID,ConsumptionKWh,Unit,BillingEnd,TotalCost,Currency,Location\nMTR-001,4500,kWh,2023-10-31,540,USD,Berlin HQ\nMTR-002,12000,kWh,2023-10-31,1440,USD,Munich Plant',
  },
  {
    key: 'travel',
    label: 'Corporate Travel',
    icon: '✈️',
    scope: 'Scope 3',
    fn: uploadTravel,
    hint: 'CSV with columns: TravelerName, FromAirport, ToAirport, FlightClass, TravelDate, Cost, Currency',
    sampleRows:
      'TravelerName,FromAirport,ToAirport,FlightClass,TravelDate,Cost,Currency\nAlice Smith,LHR,JFK,ECONOMY,2023-10-05,850,USD\nBob Jones,FRA,LHR,BUSINESS,2023-10-12,2400,EUR',
  },
];

export default function Upload() {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState({});

  const handleUpload = async (source, file) => {
    if (!file) return;

    setLoading((l) => ({ ...l, [source.key]: true }));
    setResults((r) => ({ ...r, [source.key]: null }));

    try {
      const { data } = await source.fn(file);

      setResults((r) => ({
        ...r,
        [source.key]: { success: true, data },
      }));
    } catch (err) {
      const msg = err.response?.data?.error || err.message;

      setResults((r) => ({
        ...r,
        [source.key]: { success: false, error: msg },
      }));
    } finally {
      setLoading((l) => ({ ...l, [source.key]: false }));
    }
  };

  const downloadSample = (source) => {
    const blob = new Blob([source.sampleRows], { type: 'text/csv' });

    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');

    a.href = url;
    a.download = `sample_${source.key}.csv`;

    a.click();

    URL.revokeObjectURL(url);
  };

  return (
    <div
      style={{
        padding: '8px 0 40px',
      }}
    >
      {/* Header */}
      <div
        style={{
          marginBottom: 36,
        }}
      >
        <h1
          style={{
            fontSize: 32,
            fontWeight: 800,
            marginBottom: 10,
            color: '#0f172a',
            letterSpacing: '-0.5px',
          }}
        >
          📤 Upload ESG Data
        </h1>

        <p
          style={{
            color: '#64748b',
            fontSize: 15,
            lineHeight: 1.7,
            maxWidth: 760,
          }}
        >
          Upload enterprise CSV datasets for automated emissions processing,
          normalization, and analyst review workflow.
        </p>
      </div>

      {/* Cards */}
      <div
        style={{
          display: 'grid',
          gap: 24,
        }}
      >
        {SOURCES.map((source) => (
          <div
            key={source.key}
            style={{
              background: '#ffffff',
              borderRadius: 24,
              padding: 28,
              border: '1px solid #e2e8f0',
              boxShadow: '0 10px 30px rgba(15,23,42,0.06)',
              transition: '0.25s ease',
            }}
          >
            {/* Top */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: 20,
                gap: 20,
                flexWrap: 'wrap',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  gap: 16,
                  alignItems: 'center',
                }}
              >
                {/* Icon */}
                <div
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: 18,
                    background:
                      'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 30,
                  }}
                >
                  {source.icon}
                </div>

                {/* Title */}
                <div>
                  <h2
                    style={{
                      margin: 0,
                      fontSize: 20,
                      fontWeight: 800,
                      color: '#0f172a',
                    }}
                  >
                    {source.label}
                  </h2>

                  <div
                    style={{
                      marginTop: 8,
                    }}
                  >
                    <span
                      style={{
                        background: '#f1f5f9',
                        color: '#475569',
                        padding: '6px 12px',
                        borderRadius: 999,
                        fontSize: 12,
                        fontWeight: 700,
                      }}
                    >
                      {source.scope}
                    </span>
                  </div>
                </div>
              </div>

              {/* Download Button */}
              <button
                onClick={() => downloadSample(source)}
                style={{
                  border: '1px solid #dbeafe',
                  background: '#f8fafc',
                  color: '#2563eb',
                  padding: '10px 16px',
                  borderRadius: 12,
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: 14,
                  transition: '0.2s ease',
                }}
              >
                ⬇ Download Sample CSV
              </button>
            </div>

            {/* Hint */}
            <div
              style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: 14,
                padding: 14,
                marginBottom: 22,
              }}
            >
              <p
                style={{
                  margin: 0,
                  fontSize: 13,
                  color: '#475569',
                  lineHeight: 1.6,
                  fontFamily: 'monospace',
                }}
              >
                {source.hint}
              </p>
            </div>

            {/* Upload Box */}
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                border: '2px dashed #cbd5e1',
                borderRadius: 18,
                padding: '34px 20px',
                background: '#fcfcfd',
                cursor: 'pointer',
                transition: '0.2s ease',
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  marginBottom: 10,
                }}
              >
                📁
              </div>

              <p
                style={{
                  margin: 0,
                  color: '#0f172a',
                  fontWeight: 700,
                  fontSize: 15,
                }}
              >
                Click to upload CSV
              </p>

              <span
                style={{
                  marginTop: 6,
                  color: '#64748b',
                  fontSize: 13,
                }}
              >
                Only .csv files supported
              </span>

              <input
                type="file"
                accept=".csv"
                disabled={loading[source.key]}
                onChange={(e) =>
                  handleUpload(source, e.target.files[0])
                }
                style={{
                  display: 'none',
                }}
              />
            </label>

            {/* Loading */}
            {loading[source.key] && (
              <div
                style={{
                  marginTop: 18,
                  padding: 14,
                  borderRadius: 12,
                  background: '#eff6ff',
                  color: '#2563eb',
                  fontWeight: 600,
                  fontSize: 14,
                }}
              >
                ⏳ Processing uploaded data...
              </div>
            )}

            {/* Results */}
            {results[source.key] && (
              <div
                style={{
                  marginTop: 18,
                  padding: 18,
                  borderRadius: 16,
                  background: results[source.key].success
                    ? '#f0fdf4'
                    : '#fef2f2',
                  border: `1px solid ${
                    results[source.key].success
                      ? '#bbf7d0'
                      : '#fecaca'
                  }`,
                }}
              >
                {results[source.key].success ? (
                  <>
                    <div
                      style={{
                        color: '#15803d',
                        fontWeight: 800,
                        fontSize: 16,
                        marginBottom: 12,
                      }}
                    >
                      ✅ Upload Completed Successfully
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        gap: 14,
                        flexWrap: 'wrap',
                      }}
                    >
                      <StatCard
                        label="Total Rows"
                        value={results[source.key].data.total_rows}
                      />

                      <StatCard
                        label="Success"
                        value={results[source.key].data.success_rows}
                      />

                      <StatCard
                        label="Failed"
                        value={results[source.key].data.failed_rows}
                      />
                    </div>

                    {results[source.key].data.errors?.length > 0 && (
                      <details
                        style={{
                          marginTop: 16,
                        }}
                      >
                        <summary
                          style={{
                            cursor: 'pointer',
                            fontWeight: 700,
                            color: '#92400e',
                            fontSize: 14,
                          }}
                        >
                          ⚠ View Row Errors (
                          {results[source.key].data.errors.length})
                        </summary>

                        <div
                          style={{
                            marginTop: 10,
                          }}
                        >
                          {results[source.key].data.errors.map((e, i) => (
                            <div
                              key={i}
                              style={{
                                background: '#fff7ed',
                                border: '1px solid #fed7aa',
                                padding: '10px 12px',
                                borderRadius: 10,
                                marginBottom: 8,
                                fontSize: 13,
                                color: '#c2410c',
                              }}
                            >
                              <strong>Row {e.row}:</strong> {e.error}
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </>
                ) : (
                  <div
                    style={{
                      color: '#dc2626',
                      fontWeight: 700,
                      fontSize: 15,
                    }}
                  >
                    ❌ {results[source.key].error}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid #dcfce7',
        borderRadius: 14,
        padding: '14px 18px',
        minWidth: 120,
      }}
    >
      <div
        style={{
          fontSize: 12,
          color: '#64748b',
          marginBottom: 6,
          fontWeight: 600,
        }}
      >
        {label}
      </div>

      <div
        style={{
          fontSize: 22,
          fontWeight: 800,
          color: '#166534',
        }}
      >
        {value}
      </div>
    </div>
  );
}