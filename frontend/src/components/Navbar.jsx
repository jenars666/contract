export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-left">
        <svg viewBox="0 0 24 24" className="shield-icon" aria-hidden="true">
          <path
            d="M12 2 4 5v6c0 5.2 3.4 9.8 8 11 4.6-1.2 8-5.8 8-11V5l-8-3z"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          />
          <path d="M9.2 12.4 11 14.2l4-4" fill="none" stroke="currentColor" strokeWidth="1.8" />
        </svg>
        <div className="logo-text">
          Smart<span>Patch</span>
        </div>
      </div>

      <div className="navbar-center"></div>
    </header>
  );
}
