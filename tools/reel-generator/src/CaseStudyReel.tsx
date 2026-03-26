import {
  AbsoluteFill, Audio, Img, Sequence, spring,
  useCurrentFrame, useVideoConfig, interpolate, staticFile,
} from "remotion";
import { colors, fonts } from "./brand";

const TOTAL_SECONDS = 48;

// ===== FILM GRAIN =====
const FilmGrain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{
      position: "absolute", top: 0, left: 0, width: "100%", height: "100%",
      opacity: 0.035, mixBlendMode: "overlay", pointerEvents: "none",
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' seed='${Math.floor(frame * 1.7)}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
      backgroundSize: "150px 150px",
    }} />
  );
};

const ColorGrade: React.FC = () => (
  <div style={{
    position: "absolute", top: 0, left: 0, width: "100%", height: "100%",
    background: "linear-gradient(180deg, rgba(201,169,110,0.03) 0%, transparent 30%, transparent 70%, rgba(201,169,110,0.02) 100%)",
    pointerEvents: "none", mixBlendMode: "soft-light",
  }} />
);

// ===== FLASH TRANSITION =====
const Flash: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame / dur, [0, 0.3, 1], [0, 0.7, 0], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ backgroundColor: `rgba(255,255,255,${o})`, pointerEvents: "none", zIndex: 100 }} />;
};

// ===== GOLD LINE =====
const GoldLine: React.FC<{ delay?: number; width?: number }> = ({ delay = 0, width = 160 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 15, stiffness: 100 } });
  return <div style={{ width: s * width, height: 2, backgroundColor: colors.gold, margin: "0 auto" }} />;
};

// ===== ANIMATED TEXT =====
const FadeText: React.FC<{
  children: React.ReactNode;
  delay?: number;
  style?: React.CSSProperties;
}> = ({ children, delay = 0, style = {} }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 12, stiffness: 80 } });
  return (
    <div style={{
      opacity: Math.min(s * 2.5, 1),
      transform: `translateY(${(1 - s) * 16}px)`,
      ...style,
    }}>
      {children}
    </div>
  );
};

// ===== SLIDE 1: COVER =====
const Cover: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, dur], [1.12, 1.0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/warbler_a.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center 30%",
        transform: `scale(${zoom})`,
      }} />
      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "70%",
        background: "linear-gradient(transparent, rgba(26,26,24,0.95))" }} />
      <div style={{ position: "absolute", top: 0, width: "100%", height: "20%",
        background: "linear-gradient(rgba(26,26,24,0.4), transparent)" }} />

      <div style={{ position: "absolute", bottom: 180, width: "100%", textAlign: "center", padding: "0 50px" }}>
        <FadeText delay={4} style={{
          fontFamily: fonts.display, fontSize: 28, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.35em", marginBottom: 18,
        }}>CASE STUDY</FadeText>

        <FadeText delay={10} style={{
          fontFamily: fonts.serif, fontSize: 62, fontWeight: 300,
          color: colors.paper, lineHeight: 1.15, textShadow: "0 2px 20px rgba(0,0,0,0.5)",
        }}>
          Building Balmoral's visual identity
        </FadeText>

        <FadeText delay={16}>
          <GoldLine delay={16} width={120} />
        </FadeText>

        <FadeText delay={20} style={{
          fontFamily: fonts.sans, fontSize: 24, fontWeight: 400,
          color: colors.lightStone, marginTop: 20, letterSpacing: "0.08em",
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>Photography. Website. SEO. Social.</FadeText>
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 2: THE CLIENT =====
const Client: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" });
  const imgS = spring({ frame, fps, config: { damping: 22, stiffness: 50 } });

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      {/* Photo top half */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: "50%", overflow: "hidden",
        opacity: Math.min(imgS * 2, 1),
      }}>
        <Img src={staticFile("photos/sugar_a.jpg")} style={{
          width: "100%", height: "100%", objectFit: "cover",
          transform: `scale(${zoom})`, objectPosition: "center 40%",
        }} />
        <div style={{ position: "absolute", bottom: 0, width: "100%", height: "40%",
          background: "linear-gradient(transparent, rgba(26,26,24,1))" }} />
      </div>

      {/* Text bottom half */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0, height: "55%",
        display: "flex", flexDirection: "column", justifyContent: "center",
        padding: "0 60px",
      }}>
        <FadeText delay={4} style={{
          fontFamily: fonts.display, fontSize: 22, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.3em", marginBottom: 12,
        }}>THE CLIENT</FadeText>

        <FadeText delay={8} style={{
          fontFamily: fonts.serif, fontSize: 56, fontWeight: 300,
          color: colors.paper, lineHeight: 1.1, marginBottom: 20,
        }}>Balmoral Construction</FadeText>

        <FadeText delay={12} style={{
          fontFamily: fonts.sans, fontSize: 24, fontWeight: 300,
          color: colors.lightStone, lineHeight: 1.7,
        }}>
          Custom home builder.{"\n"}Whistler & Pemberton, BC.
        </FadeText>

        <FadeText delay={18} style={{
          fontFamily: fonts.sans, fontSize: 22, fontWeight: 400,
          color: colors.stone, marginTop: 20, fontStyle: "italic",
        }}>
          4 projects. Multiple design teams.{"\n"}Zero documentation.
        </FadeText>
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 3: THE CHALLENGE =====
const Challenge: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, dur], [1.08, 1.0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/fitz_b.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center 35%",
        transform: `scale(${zoom})`, filter: "brightness(0.35)",
      }} />
      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "60%",
        background: "linear-gradient(transparent, rgba(26,26,24,0.95))" }} />

      <div style={{ position: "absolute", bottom: 200, width: "100%", padding: "0 55px" }}>
        <FadeText delay={4} style={{
          fontFamily: fonts.display, fontSize: 22, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.3em", marginBottom: 16,
        }}>THE CHALLENGE</FadeText>

        <FadeText delay={8} style={{
          fontFamily: fonts.serif, fontSize: 52, fontWeight: 300,
          color: colors.paper, lineHeight: 1.15,
          textShadow: "0 2px 15px rgba(0,0,0,0.5)",
        }}>
          Beautiful homes.
        </FadeText>
        <FadeText delay={12} style={{
          fontFamily: fonts.serif, fontSize: 52, fontWeight: 300,
          color: colors.gold, lineHeight: 1.15, fontStyle: "italic",
          textShadow: "0 2px 15px rgba(0,0,0,0.5)",
        }}>
          No documentation.
        </FadeText>

        <FadeText delay={18} style={{
          fontFamily: fonts.sans, fontSize: 22, fontWeight: 300,
          color: colors.lightStone, marginTop: 24, lineHeight: 1.7,
          textShadow: "0 1px 8px rgba(0,0,0,0.5)",
        }}>
          No photography. No web presence.{"\n"}No SEO. No social media.
        </FadeText>
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 4: PHOTOGRAPHY =====
const Photography: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const photos = ["warbler_a.jpg", "warbler_int.jpg", "eagle_a.jpg", "sugar_int.jpg"];
  const zooms = photos.map((_, i) =>
    interpolate(frame, [0, dur], [1.0, 1.0 + 0.04 * (i % 2 === 0 ? 1 : -1)], { extrapolateRight: "clamp" })
  );

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      {/* 2x2 grid */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr",
        gap: 3, width: "100%", height: "65%", position: "absolute", top: 0,
      }}>
        {photos.map((photo, i) => {
          const s = spring({ frame: frame - (2 + i * 3), fps, config: { damping: 18, stiffness: 70 } });
          return (
            <div key={photo} style={{ overflow: "hidden", opacity: Math.min(s * 2.5, 1) }}>
              <Img src={staticFile(`photos/${photo}`)} style={{
                width: "100%", height: "100%", objectFit: "cover",
                transform: `scale(${zooms[i]})`,
              }} />
            </div>
          );
        })}
      </div>

      {/* Gradient overlay */}
      <div style={{ position: "absolute", top: "45%", width: "100%", height: "55%",
        background: "linear-gradient(transparent, rgba(26,26,24,0.95) 50%)" }} />

      {/* Text */}
      <div style={{ position: "absolute", bottom: 200, width: "100%", padding: "0 55px" }}>
        <FadeText delay={6} style={{
          fontFamily: fonts.display, fontSize: 22, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.3em", marginBottom: 14,
        }}>PROJECT PHOTOGRAPHY</FadeText>

        <FadeText delay={10} style={{
          fontFamily: fonts.serif, fontSize: 52, fontWeight: 300,
          color: colors.paper, lineHeight: 1.15,
        }}>
          Four projects. <span style={{ color: colors.gold, fontStyle: "italic" }}>95 images.</span>
        </FadeText>

        <FadeText delay={16} style={{
          fontFamily: fonts.sans, fontSize: 22, fontWeight: 300,
          color: colors.lightStone, marginTop: 16, lineHeight: 1.6,
        }}>
          Exteriors, interiors, drone, twilight,{"\n"}and material details across{"\n"}Whistler and Pemberton.
        </FadeText>
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 5: WEBSITE =====
const Website: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = frame / dur;

  // Browser frame slides up
  const browserS = spring({ frame: frame - 4, fps, config: { damping: 18, stiffness: 55 } });

  // Website scroll
  const scrollPx = interpolate(progress,
    [0.1, 0.2, 0.4, 0.5, 0.7, 0.8, 1],
    [0, 0, 600, 600, 1200, 1200, 1200],
    { extrapolateRight: "clamp" });

  // Stat counter
  const countStart = 0.35;
  const pageCount = Math.round(interpolate(progress, [countStart, countStart + 0.15], [0, 42],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const statOp = interpolate(progress, [countStart - 0.02, countStart + 0.05, 0.6, 0.7], [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #1f1f1d 0%, ${colors.ink} 80%)`,
      }} />

      {/* Header text */}
      <div style={{ position: "absolute", top: 100, width: "100%", textAlign: "center", padding: "0 50px" }}>
        <FadeText delay={2} style={{
          fontFamily: fonts.display, fontSize: 22, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.3em", marginBottom: 14,
        }}>WEBSITE REBUILD</FadeText>

        <FadeText delay={6} style={{
          fontFamily: fonts.serif, fontSize: 50, fontWeight: 300,
          color: colors.paper, lineHeight: 1.15,
        }}>
          42 pages. <span style={{ color: colors.gold, fontStyle: "italic" }}>Custom coded.</span>
        </FadeText>
      </div>

      {/* Browser mockup */}
      <div style={{
        position: "absolute", top: 320, left: 40, right: 40, bottom: 200,
        opacity: Math.min(browserS * 2, 1),
        transform: `translateY(${(1 - browserS) * 60}px)`,
      }}>
        <div style={{
          background: "#222", borderRadius: 12, overflow: "hidden",
          boxShadow: "0 30px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)",
          height: "100%", display: "flex", flexDirection: "column",
        }}>
          {/* Browser bar */}
          <div style={{
            background: "#2a2a2a", padding: "10px 16px",
            display: "flex", alignItems: "center", gap: 8,
            borderBottom: "1px solid rgba(255,255,255,0.06)", flexShrink: 0,
          }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff5f57" }} />
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#ffbd2e" }} />
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#28c840" }} />
            <div style={{
              flex: 1, marginLeft: 12, background: "rgba(255,255,255,0.06)",
              borderRadius: 4, padding: "5px 14px",
              fontFamily: fonts.sans, fontSize: 14, color: "rgba(255,255,255,0.35)",
            }}>balmoralconstruction.com</div>
          </div>
          {/* Scrolling content */}
          <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>
            <div style={{ position: "absolute", top: 0, left: 0, width: "100%",
              transform: `translateY(${-scrollPx}px)` }}>
              <Img src={staticFile("photos/website.png")} style={{ width: "100%", display: "block" }} />
            </div>
          </div>
        </div>
      </div>

      {/* Stat badge */}
      {statOp > 0 && (
        <div style={{
          position: "absolute", bottom: 220, width: "100%", textAlign: "center", opacity: statOp,
        }}>
          <div style={{
            display: "inline-block", backgroundColor: "rgba(0,0,0,0.88)",
            borderRadius: 10, padding: "10px 45px", borderTop: `3px solid ${colors.gold}`,
            boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
          }}>
            <span style={{ fontFamily: fonts.display, fontSize: 50, fontWeight: 700, color: colors.gold }}>{pageCount}</span>
            <span style={{ fontFamily: fonts.display, fontSize: 22, fontWeight: 700, color: colors.paper, letterSpacing: "0.15em", marginLeft: 14 }}>PAGES</span>
          </div>
        </div>
      )}

      {/* Bottom text */}
      <div style={{ position: "absolute", bottom: 120, width: "100%", textAlign: "center" }}>
        <FadeText delay={Math.round(dur * 0.6)} style={{
          fontFamily: fonts.sans, fontSize: 20, fontWeight: 300,
          color: colors.stone, lineHeight: 1.6,
        }}>
          14 project galleries. 6 service pages.{"\n"}6 location pages. 7 blog posts.
        </FadeText>
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 6: SEO =====
const SEO: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cards = [
    { title: "LOCATION PAGES", body: "6 geo-targeted for Whistler,\nPemberton & Squamish" },
    { title: "BLOG CONTENT", body: "7 SEO posts answering\nreal buyer questions" },
    { title: "STRUCTURED DATA", body: "JSON-LD schema\non every page" },
    { title: "MONTHLY RETAINER", body: "Ongoing optimization\nand content strategy" },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #1f1f1d 0%, ${colors.ink} 80%)`,
      }} />

      <div style={{ position: "absolute", top: 160, width: "100%", textAlign: "center", padding: "0 50px" }}>
        <FadeText delay={3} style={{
          fontFamily: fonts.display, fontSize: 22, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.3em", marginBottom: 14,
        }}>SEO & CONTENT</FadeText>

        <FadeText delay={7} style={{
          fontFamily: fonts.serif, fontSize: 50, fontWeight: 300,
          color: colors.paper, lineHeight: 1.15,
        }}>
          Found where it <span style={{ color: colors.gold, fontStyle: "italic" }}>matters.</span>
        </FadeText>
      </div>

      {/* Cards 2x2 */}
      <div style={{
        position: "absolute", top: 420, left: 45, right: 45,
        display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16,
      }}>
        {cards.map((card, i) => {
          const s = spring({ frame: frame - (12 + i * 4), fps, config: { damping: 14, stiffness: 80 } });
          return (
            <div key={card.title} style={{
              border: `1px solid ${colors.goldBorder || "rgba(201,169,110,0.25)"}`,
              borderRadius: 8, padding: 24,
              background: "rgba(201,169,110,0.03)",
              opacity: Math.min(s * 2.5, 1),
              transform: `translateY(${(1 - s) * 20}px)`,
            }}>
              <div style={{
                fontFamily: fonts.display, fontSize: 16, fontWeight: 700,
                color: colors.gold, letterSpacing: "0.12em", marginBottom: 10,
              }}>{card.title}</div>
              <div style={{
                fontFamily: fonts.sans, fontSize: 18, fontWeight: 300,
                color: colors.lightStone, lineHeight: 1.5, whiteSpace: "pre-line",
              }}>{card.body}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 7: SOCIAL MEDIA =====
const Social: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" });
  const imgS = spring({ frame, fps, config: { damping: 22, stiffness: 50 } });

  const channels = [
    { name: "INSTAGRAM", detail: "8-week calendar" },
    { name: "LINKEDIN", detail: "14 posts queued" },
    { name: "PINTEREST", detail: "25 pins deployed" },
    { name: "VIDEO", detail: "Animated reel" },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      {/* Photo top */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: "45%", overflow: "hidden",
        opacity: Math.min(imgS * 2, 1),
      }}>
        <Img src={staticFile("photos/warbler_twilight.jpg")} style={{
          width: "100%", height: "100%", objectFit: "cover",
          transform: `scale(${zoom})`, objectPosition: "center",
        }} />
        <div style={{ position: "absolute", bottom: 0, width: "100%", height: "50%",
          background: "linear-gradient(transparent, rgba(26,26,24,1))" }} />
      </div>

      {/* Text */}
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "60%",
        display: "flex", flexDirection: "column", justifyContent: "center", padding: "0 55px" }}>

        <FadeText delay={4} style={{
          fontFamily: fonts.display, fontSize: 22, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.3em", marginBottom: 14,
        }}>SOCIAL MEDIA</FadeText>

        <FadeText delay={8} style={{
          fontFamily: fonts.serif, fontSize: 48, fontWeight: 300,
          color: colors.paper, lineHeight: 1.15, marginBottom: 30,
        }}>
          From zero to{"\n"}<span style={{ color: colors.gold, fontStyle: "italic" }}>multi-channel.</span>
        </FadeText>

        {/* Timeline */}
        <div style={{ position: "relative", paddingLeft: 28 }}>
          {/* Gold line */}
          <div style={{
            position: "absolute", left: 5, top: 0,
            width: 2, backgroundColor: colors.gold,
            height: `${interpolate(
              spring({ frame: frame - 12, fps, config: { damping: 15, stiffness: 60 } }),
              [0, 1], [0, 100]
            )}%`,
          }} />

          {channels.map((ch, i) => {
            const s = spring({ frame: frame - (14 + i * 5), fps, config: { damping: 14, stiffness: 80 } });
            return (
              <div key={ch.name} style={{
                marginBottom: 22, opacity: Math.min(s * 2.5, 1),
                transform: `translateX(${(1 - s) * -16}px)`,
              }}>
                {/* Dot */}
                <div style={{
                  position: "absolute", left: 0, width: 12, height: 12,
                  borderRadius: "50%", border: `2px solid ${colors.gold}`,
                  backgroundColor: colors.ink, marginTop: 4,
                }} />
                <div style={{
                  fontFamily: fonts.display, fontSize: 18, fontWeight: 700,
                  color: colors.gold, letterSpacing: "0.12em",
                }}>{ch.name}</div>
                <div style={{
                  fontFamily: fonts.sans, fontSize: 20, fontWeight: 300,
                  color: colors.lightStone,
                }}>{ch.detail}</div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 8: PARTNERSHIP MODEL =====
const Partnership: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, dur], [1.1, 1.0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/warbler_wide.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center",
        transform: `scale(${zoom})`, filter: "brightness(0.25)",
      }} />
      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "65%",
        background: "linear-gradient(transparent, rgba(26,26,24,0.95))" }} />

      <div style={{
        position: "absolute", width: "100%", height: "100%",
        display: "flex", flexDirection: "column", justifyContent: "center",
        alignItems: "center", textAlign: "center", padding: "0 50px",
      }}>
        <FadeText delay={4} style={{
          fontFamily: fonts.display, fontSize: 22, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.3em", marginBottom: 16,
        }}>THE MODEL</FadeText>

        <FadeText delay={8} style={{
          fontFamily: fonts.serif, fontSize: 52, fontWeight: 300,
          color: colors.paper, lineHeight: 1.15,
          textShadow: "0 2px 20px rgba(0,0,0,0.5)",
        }}>
          Not a vendor.
        </FadeText>
        <FadeText delay={14} style={{
          fontFamily: fonts.serif, fontSize: 52, fontWeight: 300,
          color: colors.gold, fontStyle: "italic", lineHeight: 1.15, marginTop: 4,
          textShadow: "0 2px 20px rgba(0,0,0,0.5)",
        }}>
          A creative partner.
        </FadeText>

        <FadeText delay={18}>
          <GoldLine delay={18} width={100} />
        </FadeText>

        <FadeText delay={22} style={{
          fontFamily: fonts.sans, fontSize: 22, fontWeight: 300,
          color: colors.lightStone, marginTop: 24, lineHeight: 1.7,
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>
          Photography, website, SEO, and social{"\n"}in one monthly relationship.
        </FadeText>
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 9: RESULTS =====
const Results: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = frame / dur;

  const stats = [
    { target: 4, label: "PROJECTS\nSHOT" },
    { target: 95, label: "IMAGES\nDELIVERED" },
    { target: 42, label: "WEBSITE\nPAGES" },
    { target: 7, label: "BLOG\nPOSTS" },
    { target: 6, label: "SEO\nPAGES" },
    { target: 53, label: "SOCIAL\nPOSTS" },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #1f1f1d 0%, ${colors.ink} 80%)`,
      }} />

      <div style={{ position: "absolute", top: 160, width: "100%", textAlign: "center" }}>
        <FadeText delay={3} style={{
          fontFamily: fonts.display, fontSize: 22, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.3em", marginBottom: 14,
        }}>BY THE NUMBERS</FadeText>

        <FadeText delay={7} style={{
          fontFamily: fonts.serif, fontSize: 50, fontWeight: 300,
          color: colors.paper,
        }}>
          The <span style={{ color: colors.gold, fontStyle: "italic" }}>results.</span>
        </FadeText>
      </div>

      {/* 3x2 grid */}
      <div style={{
        position: "absolute", top: 400, left: 40, right: 40,
        display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "50px 20px",
      }}>
        {stats.map((stat, i) => {
          const delay = 10 + i * 4;
          const s = spring({ frame: frame - delay, fps, config: { damping: 12, stiffness: 80 } });
          const count = Math.round(interpolate(
            spring({ frame: frame - delay, fps, config: { damping: 20, stiffness: 40 } }),
            [0, 1], [0, stat.target]
          ));

          return (
            <div key={stat.label} style={{
              textAlign: "center",
              opacity: Math.min(s * 2.5, 1),
              transform: `translateY(${(1 - s) * 20}px)`,
            }}>
              <div style={{
                fontFamily: fonts.serif, fontSize: 72, fontWeight: 400,
                color: colors.gold, lineHeight: 1,
              }}>{count}</div>
              <div style={{
                fontFamily: fonts.display, fontSize: 14, fontWeight: 700,
                color: colors.stone, letterSpacing: "0.2em", marginTop: 8,
                lineHeight: 1.4, whiteSpace: "pre-line",
              }}>{stat.label}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ===== SLIDE 10: CTA =====
const CTA: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, dur], [1.05, 1.15], { extrapolateRight: "clamp" });
  const ctaFrame = frame;
  const pulse = ctaFrame > 40 ? 1 + Math.sin((ctaFrame - 40) * 0.06) * 0.015 : 1;

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/warbler_a.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center",
        transform: `scale(${zoom})`, transformOrigin: "center center",
        filter: "brightness(0.2) saturate(0.7)",
      }} />
      <div style={{ position: "absolute", width: "100%", height: "100%",
        background: "linear-gradient(rgba(26,26,24,0.3) 0%, rgba(26,26,24,0.8) 45%, rgba(26,26,24,0.95) 100%)" }} />

      <div style={{
        position: "absolute", width: "100%", height: "100%",
        display: "flex", flexDirection: "column", justifyContent: "center",
        alignItems: "center", textAlign: "center", padding: "0 50px",
      }}>
        <FadeText delay={4}>
          <GoldLine delay={4} width={180} />
        </FadeText>

        <FadeText delay={8} style={{
          fontFamily: fonts.serif, fontSize: 48, fontWeight: 300,
          color: colors.paper, lineHeight: 1.25, marginTop: 30,
          textShadow: "0 2px 25px rgba(0,0,0,0.6)",
        }}>
          Your projects deserve{"\n"}this level of documentation.
        </FadeText>

        <FadeText delay={16} style={{
          fontFamily: fonts.sans, fontSize: 22, fontWeight: 400,
          color: colors.lightStone, marginTop: 18,
          textShadow: "0 1px 15px rgba(0,0,0,0.5)",
        }}>
          Let's talk about what you're building.
        </FadeText>

        <FadeText delay={22} style={{
          marginTop: 40, transform: `scale(${pulse})`,
        }}>
          <div style={{
            fontFamily: fonts.display, fontSize: 24, fontWeight: 700,
            color: colors.ink, letterSpacing: "0.1em",
            backgroundColor: colors.gold, borderRadius: 8,
            padding: "16px 45px", display: "inline-block",
            boxShadow: "0 8px 35px rgba(201,169,110,0.35)",
          }}>VIEW FULL CASE STUDY</div>
        </FadeText>

        <FadeText delay={28} style={{
          fontFamily: fonts.sans, fontSize: 20, color: colors.gold,
          marginTop: 24, letterSpacing: "0.02em",
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>mattanthonyphoto.com</FadeText>

        <FadeText delay={32} style={{
          fontFamily: fonts.sans, fontSize: 22, fontWeight: 500,
          color: colors.stone, marginTop: 14,
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>@mattanthonyphoto</FadeText>
      </div>
    </AbsoluteFill>
  );
};

// ===== MAIN COMPOSITION =====
export const CaseStudyReel: React.FC = () => {
  const { fps } = useVideoConfig();
  const FLASH_DUR = 3;

  // Slide durations in frames (30fps)
  // Total = 48 seconds = 1440 frames
  const COVER_DUR = 5 * fps;      // 150 - needs time to read
  const CLIENT_DUR = 5 * fps;     // 150
  const CHALLENGE_DUR = 4.5 * fps; // 135
  const PHOTO_DUR = 5 * fps;      // 150
  const WEB_DUR = 6 * fps;        // 180 - website scroll needs time
  const SEO_DUR = 5 * fps;        // 150
  const SOCIAL_DUR = 5.5 * fps;   // 165
  const PARTNER_DUR = 5 * fps;    // 150
  const RESULTS_DUR = 5 * fps;    // 150
  const CTA_DUR = 6 * fps;        // 180 - let it breathe at end

  // Frame offsets
  let f = 0;
  const s = (dur: number) => { const start = f; f += dur; return { start, dur }; };

  const cover = s(COVER_DUR);
  const client = s(CLIENT_DUR);
  const challenge = s(CHALLENGE_DUR);
  const photo = s(PHOTO_DUR);
  const web = s(WEB_DUR);
  const seo = s(SEO_DUR);
  const social = s(SOCIAL_DUR);
  const partner = s(PARTNER_DUR);
  const results = s(RESULTS_DUR);
  const cta = s(CTA_DUR);

  const flash = (at: number) => (
    <Sequence from={at - FLASH_DUR} durationInFrames={FLASH_DUR + 2}>
      <Flash dur={FLASH_DUR + 2} />
    </Sequence>
  );

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Audio
        src={staticFile("music.mp3")}
        volume={(f) => {
          const fadeIn = Math.min(f / (0.5 * 30), 1);
          const fadeOutStart = (TOTAL_SECONDS - 3) * 30;
          const fadeOut = f > fadeOutStart ? 1 - ((f - fadeOutStart) / (3 * 30)) : 1;
          return 0.7 * fadeIn * Math.max(0, fadeOut);
        }}
      />

      <Sequence from={cover.start} durationInFrames={cover.dur}><Cover dur={cover.dur} /></Sequence>
      {flash(cover.start + cover.dur)}

      <Sequence from={client.start} durationInFrames={client.dur}><Client dur={client.dur} /></Sequence>
      {flash(client.start + client.dur)}

      <Sequence from={challenge.start} durationInFrames={challenge.dur}><Challenge dur={challenge.dur} /></Sequence>
      {flash(challenge.start + challenge.dur)}

      <Sequence from={photo.start} durationInFrames={photo.dur}><Photography dur={photo.dur} /></Sequence>
      {flash(photo.start + photo.dur)}

      <Sequence from={web.start} durationInFrames={web.dur}><Website dur={web.dur} /></Sequence>
      {flash(web.start + web.dur)}

      <Sequence from={seo.start} durationInFrames={seo.dur}><SEO dur={seo.dur} /></Sequence>
      {flash(seo.start + seo.dur)}

      <Sequence from={social.start} durationInFrames={social.dur}><Social dur={social.dur} /></Sequence>
      {flash(social.start + social.dur)}

      <Sequence from={partner.start} durationInFrames={partner.dur}><Partnership dur={partner.dur} /></Sequence>
      {flash(partner.start + partner.dur)}

      <Sequence from={results.start} durationInFrames={results.dur}><Results dur={results.dur} /></Sequence>
      {flash(results.start + results.dur)}

      <Sequence from={cta.start} durationInFrames={cta.dur}><CTA dur={cta.dur} /></Sequence>

      {/* Global overlays */}
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><FilmGrain /></Sequence>
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><ColorGrade /></Sequence>
    </AbsoluteFill>
  );
};
