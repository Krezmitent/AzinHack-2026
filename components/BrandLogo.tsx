export default function BrandLogo() {
  return (
    <span className="brand-lockup" aria-hidden="true">
      <svg className="brand-symbol" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M6 34.5 17.7 7h7.1L13.2 34.5H6Z" fill="currentColor" />
        <path d="m24.8 7 11.6 27.5h-7.2L21.3 15l3.5-8Z" fill="currentColor" />
        <path d="M19.3 25.7h10.1" stroke="var(--brand-cut, #3F5BFF)" strokeWidth="5.2" strokeLinecap="square" />
        <path d="M32.6 4.5h5.1v5.1h-5.1z" fill="var(--brand-accent, #FF775C)" />
      </svg>
      <span className="brand-wordmark">auto<span>grant</span></span>
    </span>
  );
}
