import { NavLink } from 'react-router-dom';

const links = [
  { to: '/dashboard', label: '📊 Dashboard' },
  { to: '/upload', label: '📤 Upload' },
  { to: '/review', label: '🔍 Review Queue' },
  { to: '/approved', label: '✅ Approved' },
];

export default function Navbar() {
  return (
    <nav
      style={{
        background: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(10px)',
        padding: '0 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: 72,
        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
      }}
    >
      {/* Logo */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: 12,
            background: 'linear-gradient(135deg, #22c55e, #16a34a)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 20,
            boxShadow: '0 4px 12px rgba(34,197,94,0.35)',
          }}
        >
          🌱
        </div>

        <div>
          <div
            style={{
              color: '#f8fafc',
              fontWeight: 800,
              fontSize: 18,
              letterSpacing: 0.4,
            }}
          >
            Breathe ESG
          </div>

          <div
            style={{
              color: '#94a3b8',
              fontSize: 11,
              marginTop: 2,
            }}
          >
            Sustainability Dashboard
          </div>
        </div>
      </div>

      {/* Links */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#cbd5e1',
              textDecoration: 'none',
              padding: '10px 18px',
              borderRadius: 12,
              fontSize: 14,
              fontWeight: isActive ? 700 : 500,
              background: isActive
                ? 'linear-gradient(135deg, #22c55e, #16a34a)'
                : 'transparent',
              boxShadow: isActive
                ? '0 4px 14px rgba(34,197,94,0.35)'
                : 'none',
              transition: 'all 0.25s ease',
              border: isActive
                ? '1px solid rgba(255,255,255,0.12)'
                : '1px solid transparent',
            })}
          >
            {l.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}