interface Props {
  size?: number;
  showText?: boolean;
  textSize?: number;
  className?: string;
}

export default function EduAILogo({
  size = 40,
  showText = true,
  textSize,
  className = "",
}: Props) {
  const ts = textSize ?? size * 0.52;
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 64 64"
        width={size}
        height={size}
        style={{ flexShrink: 0 }}
      >
        <defs>
          <linearGradient id="edu-brand-g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#E07A3C" />
            <stop offset="100%" stopColor="#C45A1F" />
          </linearGradient>
        </defs>
        <rect
          x="2"
          y="2"
          width="60"
          height="60"
          rx="14"
          fill="url(#edu-brand-g)"
        />
        <path
          d="M19 18 H45 V25 H27 V29 H42 V35 H27 V39 H45 V46 H19 Z"
          fill="#FFFFFF"
        />
        <circle cx="48" cy="18" r="4" fill="#FFE7A3" />
        <circle cx="48" cy="18" r="2" fill="#FFFFFF" />
      </svg>
      {showText && (
        <span
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontWeight: 700,
            fontSize: ts,
            color: "#F2EDE7",
            letterSpacing: "-0.02em",
            lineHeight: 1,
          }}
        >
          EduAI
        </span>
      )}
    </div>
  );
}
