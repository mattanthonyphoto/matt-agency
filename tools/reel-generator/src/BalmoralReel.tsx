import {
  AbsoluteFill, Audio, Img, Sequence, spring,
  useCurrentFrame, useVideoConfig, interpolate, staticFile,
} from "remotion";
import { colors, fonts, slides, type Slide } from "./brand";

const TOTAL_SECONDS = 23;

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

// ===== WARM COLOR GRADE — subtle cinematic warmth =====
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
  const o = interpolate(frame / dur, [0, 0.3, 1], [0, 0.8, 0], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ backgroundColor: `rgba(255,255,255,${o})`, pointerEvents: "none", zIndex: 100 }} />;
};

// ===== HOOK =====
const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgPhotos = ["warbler_a.jpg", "fitz_a.jpg", "sugar_a.jpg", "eagle_a.jpg"];
  const photoIndex = Math.floor(frame / 7) % 4;
  const bgOpacity = interpolate(frame, [0, 8, 42, 52], [0, 0.12, 0.12, 0], { extrapolateRight: "clamp" });

  const t1 = spring({ frame: frame - 4, fps, config: { damping: 12, stiffness: 80 } });
  const t2 = spring({ frame: frame - 13, fps, config: { damping: 12, stiffness: 70 } });
  const line = spring({ frame: frame - 20, fps, config: { damping: 15, stiffness: 100 } }) * 160;

  // Subtle scale breathe on the whole thing
  const breathe = 1 + Math.sin(frame * 0.04) * 0.005;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      {bgPhotos.map((photo, i) => (
        <Img key={photo} src={staticFile(`photos/${photo}`)} style={{
          position: "absolute", width: "100%", height: "100%",
          objectFit: "cover", filter: "blur(10px) brightness(0.15) saturate(0.6)",
          opacity: i === photoIndex ? bgOpacity : 0,
        }} />
      ))}
      <div style={{
        position: "relative", zIndex: 1, display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center", height: "100%",
        transform: `scale(${breathe})`,
      }}>
        <div style={{ opacity: Math.min(t1*2.5,1), transform: `translateY(${(1-t1)*18}px)`,
          fontFamily: fonts.display, fontSize: 44, fontWeight: 700,
          color: colors.stone, letterSpacing: "0.15em", textAlign: "center" }}>
          ONE CLIENT. ONE YEAR.
        </div>
        <div style={{ opacity: Math.min(t2*2,1), transform: `translateY(${(1-t2)*18}px)`,
          fontFamily: fonts.serif, fontSize: 78, fontWeight: 300,
          color: colors.paper, marginTop: 10, textAlign: "center" }}>
          Everything.
        </div>
        <div style={{ width: line, height: 3, backgroundColor: colors.gold, marginTop: 25 }} />
      </div>
    </AbsoluteFill>
  );
};

// ===== LABEL =====
const Label: React.FC<{ label: string; location?: string; dur: number }> = ({ label, location, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const i = spring({ frame: frame - 4, fps, config: { damping: 14, stiffness: 90 } });
  const o = interpolate(frame, [dur - 5, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const op = Math.min(i, o);

  return (
    <div style={{ position: "absolute", bottom: 200, width: "100%", textAlign: "center",
      opacity: op, transform: `translateY(${(1-i)*12}px)` }}>
      <div style={{ width: 180, height: 2, backgroundColor: colors.gold, margin: "0 auto 14px", opacity: op }} />
      <div style={{ fontFamily: fonts.display, fontSize: 40, fontWeight: 700,
        color: colors.paper, letterSpacing: "0.1em", textShadow: "0 2px 15px rgba(0,0,0,0.6)" }}>{label}</div>
      {location && <div style={{ fontFamily: fonts.sans, fontSize: 23, fontWeight: 500,
        color: colors.gold, marginTop: 8, letterSpacing: "0.05em", textShadow: "0 1px 10px rgba(0,0,0,0.6)" }}>{location}</div>}
    </div>
  );
};

// ===== FULLSCREEN =====
const Fullscreen: React.FC<{ slide: Slide; dur: number }> = ({ slide, dur }) => {
  const frame = useCurrentFrame();
  const zoom = slide.zoomDir === "out"
    ? interpolate(frame, [0, dur], [1.15, 1.0], { extrapolateRight: "clamp" })
    : interpolate(frame, [0, dur], [1.0, 1.12], { extrapolateRight: "clamp" });
  const drift = interpolate(frame, [0, dur], [-0.8, 0.8], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile(`photos/${slide.photos[0]}`)} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center 30%",
        transform: `scale(${zoom}) translateY(${drift}%)`,
        transformOrigin: "center center" }} />
      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "45%",
        background: "linear-gradient(transparent, rgba(0,0,0,0.75))" }} />
      <div style={{ position: "absolute", top: 0, width: "100%", height: "15%",
        background: "linear-gradient(rgba(0,0,0,0.3), transparent)" }} />
      {slide.label && <Label label={slide.label} location={slide.location} dur={dur} />}
    </AbsoluteFill>
  );
};

// ===== HORIZONTAL FLOAT =====
const HorizontalFloat: React.FC<{ slide: Slide; dur: number }> = ({ slide, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pos = slide.floatPos || "center";

  const zoom = slide.zoomDir === "out"
    ? interpolate(frame, [0, dur], [1.06, 1.0], { extrapolateRight: "clamp" })
    : interpolate(frame, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" });

  const si = spring({ frame, fps, config: { damping: 22, stiffness: 50 } });
  const fromY = pos === "top" ? -120 : pos === "bottom" ? 120 : 0;
  const fromX = pos === "center" ? 120 : 0;
  const y = (1 - si) * fromY;
  const x = (1 - si) * fromX;
  const rotate = (1 - si) * (pos === "top" ? -1.5 : pos === "bottom" ? 1.5 : -1);

  const topMap = { top: "10%", center: "30%", bottom: "42%" };
  const shadowO = interpolate(si, [0, 1], [0, 0.7]);

  // Subtle hover float after landing
  const hover = Math.sin(frame * 0.06) * 3;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink, overflow: "hidden" }}>
      <div style={{ position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #1f1f1d 0%, ${colors.ink} 80%)` }} />
      <div style={{
        position: "absolute", top: topMap[pos], left: "4%", right: "4%",
        transform: `translate(${x}px, ${y + (si > 0.95 ? hover : 0)}px) rotate(${rotate}deg)`,
        borderRadius: 6, overflow: "hidden",
        boxShadow: `0 30px 80px rgba(0,0,0,${shadowO}), 0 12px 35px rgba(0,0,0,${shadowO * 0.7})`,
      }}>
        <Img src={staticFile(`photos/${slide.photos[0]}`)} style={{
          width: "100%", display: "block",
          transform: `scale(${zoom})`, transformOrigin: "center center" }} />
      </div>
      {slide.label && <Label label={slide.label} location={slide.location} dur={dur} />}
    </AbsoluteFill>
  );
};

// ===== STACKED PAIR =====
const StackedPair: React.FC<{ slide: Slide; dur: number }> = ({ slide, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s1 = spring({ frame: frame - 1, fps, config: { damping: 20, stiffness: 55 } });
  const s2 = spring({ frame: frame - 7, fps, config: { damping: 20, stiffness: 55 } });
  const z1 = interpolate(frame, [0, dur], [1.0, 1.04], { extrapolateRight: "clamp" });
  const z2 = interpolate(frame, [0, dur], [1.04, 1.0], { extrapolateRight: "clamp" });
  const r1 = (1 - s1) * -2.5;
  const r2 = (1 - s2) * 2;
  const shadow = `0 20px 60px rgba(0,0,0,0.6), 0 8px 25px rgba(0,0,0,0.4)`;

  // Subtle counter-hover
  const h1 = Math.sin(frame * 0.05) * 2;
  const h2 = Math.cos(frame * 0.05) * 2;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink, overflow: "hidden" }}>
      <div style={{ position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #1f1f1d 0%, ${colors.ink} 80%)` }} />
      <div style={{
        position: "absolute", top: "14%", left: "3%", right: "12%",
        transform: `translateX(${(1-s1)*-180}px) translateY(${s1>0.95?h1:0}px) rotate(${r1}deg)`,
        borderRadius: 6, overflow: "hidden", boxShadow: shadow, opacity: Math.min(s1*3,1),
      }}>
        <Img src={staticFile(`photos/${slide.photos[0]}`)} style={{
          width: "100%", display: "block", transform: `scale(${z1})`, transformOrigin: "center center" }} />
      </div>
      <div style={{
        position: "absolute", top: "53%", left: "12%", right: "3%",
        transform: `translateX(${(1-s2)*180}px) translateY(${s2>0.95?h2:0}px) rotate(${r2}deg)`,
        borderRadius: 6, overflow: "hidden", boxShadow: shadow, opacity: Math.min(s2*3,1),
      }}>
        <Img src={staticFile(`photos/${slide.photos[1]}`)} style={{
          width: "100%", display: "block", transform: `scale(${z2})`, transformOrigin: "center center" }} />
      </div>
      <div style={{
        position: "absolute", top: "51%", left: "10%",
        width: `${interpolate(Math.min(s1,s2), [0,1], [0,80])}%`,
        height: 2, backgroundColor: colors.gold, opacity: Math.min(s1,s2)*0.8,
      }} />
    </AbsoluteFill>
  );
};

// ===== BIG + SMALL =====
const BigSmall: React.FC<{ slide: Slide; dur: number }> = ({ slide, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s1 = spring({ frame: frame - 1, fps, config: { damping: 18, stiffness: 60 } });
  const s2 = spring({ frame: frame - 8, fps, config: { damping: 18, stiffness: 60 } });
  const z1 = interpolate(frame, [0, dur], [1.0, 1.05], { extrapolateRight: "clamp" });
  const z2 = interpolate(frame, [0, dur], [1.05, 1.0], { extrapolateRight: "clamp" });
  const r1 = (1 - s1) * -1.5;
  const r2 = (1 - s2) * 2;
  const shadow = `0 20px 60px rgba(0,0,0,0.6)`;
  const h1 = Math.sin(frame * 0.05) * 2;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink, overflow: "hidden" }}>
      <div style={{ position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #1f1f1d 0%, ${colors.ink} 80%)` }} />
      <div style={{
        position: "absolute", top: "8%", left: "4%", right: "4%",
        transform: `translateY(${(1-s1)*-120 + (s1>0.95?h1:0)}px) rotate(${r1}deg)`,
        borderRadius: 6, overflow: "hidden", boxShadow: shadow, opacity: Math.min(s1*3,1),
      }}>
        <Img src={staticFile(`photos/${slide.photos[0]}`)} style={{
          width: "100%", display: "block", transform: `scale(${z1})`, transformOrigin: "center center" }} />
      </div>
      <div style={{
        position: "absolute", bottom: "12%", right: "6%", width: "48%",
        transform: `translateX(${(1-s2)*120}px) rotate(${r2}deg)`,
        borderRadius: 6, overflow: "hidden", boxShadow: shadow, opacity: Math.min(s2*3,1),
      }}>
        <Img src={staticFile(`photos/${slide.photos[1]}`)} style={{
          width: "100%", display: "block", transform: `scale(${z2})`, transformOrigin: "center center" }} />
      </div>
      <div style={{
        position: "absolute", bottom: "10%", left: "6%",
        width: `${interpolate(s2, [0,1], [0,40])}%`,
        height: 2, backgroundColor: colors.gold, opacity: s2*0.8,
      }} />
      {slide.label && <Label label={slide.label} location={slide.location} dur={dur} />}
    </AbsoluteFill>
  );
};

// ===== WEBSITE SCROLL =====
const WebsiteScroll: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = frame / dur;

  const scrollPx = interpolate(progress,
    [0, 0.06, 0.22, 0.32, 0.48, 0.58, 0.78, 0.88, 1],
    [0, 0, 1200, 1200, 2800, 2800, 4200, 4633, 4633]);
  const zoom = interpolate(progress, [0, 0.06], [1.06, 1.0], { extrapolateRight: "clamp" });

  const s1P = interpolate(progress, [0.18,0.24,0.28,0.34], [0,1,1,0], { extrapolateLeft:"clamp", extrapolateRight:"clamp" });
  const s2P = interpolate(progress, [0.44,0.50,0.54,0.60], [0,1,1,0], { extrapolateLeft:"clamp", extrapolateRight:"clamp" });
  const s3P = interpolate(progress, [0.74,0.80,0.84,0.90], [0,1,1,0], { extrapolateLeft:"clamp", extrapolateRight:"clamp" });

  const c1 = Math.round(interpolate(progress, [0.18,0.26], [0,42], { extrapolateLeft:"clamp", extrapolateRight:"clamp" }));
  const c2 = Math.round(interpolate(progress, [0.44,0.52], [0,14], { extrapolateLeft:"clamp", extrapolateRight:"clamp" }));
  const c3 = Math.round(interpolate(progress, [0.74,0.82], [0,6], { extrapolateLeft:"clamp", extrapolateRight:"clamp" }));

  const StatBadge: React.FC<{ num: number; label: string; opacity: number }> = ({ num, label, opacity }) => {
    const sc = spring({ frame: Math.round(opacity * 30), fps, config: { damping: 12, stiffness: 100 } });
    return (
      <div style={{ position: "absolute", bottom: 180, width: "100%", textAlign: "center", opacity,
        transform: `scale(${0.85 + sc * 0.15})` }}>
        <div style={{
          display: "inline-block", backgroundColor: "rgba(0,0,0,0.88)",
          borderRadius: 10, padding: "12px 50px", borderTop: `3px solid ${colors.gold}`,
          boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
        }}>
          <div style={{ fontFamily: fonts.display, fontSize: 64, fontWeight: 700, color: colors.gold }}>{num}</div>
          <div style={{ fontFamily: fonts.display, fontSize: 24, fontWeight: 700, color: colors.paper, letterSpacing: "0.15em" }}>{label}</div>
        </div>
      </div>
    );
  };

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 6553,
        transform: `scale(${zoom}) translateY(${-scrollPx}px)`, transformOrigin: "center top",
      }}>
        <Img src={staticFile("photos/website.png")} style={{ width: "100%" }} />
      </div>
      <StatBadge num={c1} label="PAGES" opacity={s1P} />
      <StatBadge num={c2} label="GALLERIES" opacity={s2P} />
      <StatBadge num={c3} label="LOCATIONS" opacity={s3P} />
    </AbsoluteFill>
  );
};

// ===== END CARD + CTA COMBINED — smooth crossfade between them =====
const EndSection: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const services = ["PHOTOGRAPHY", "VIDEO", "DRONE", "WEBSITE", "SEO", "STRATEGY", "RETAINER"];

  // Tighter split: stack 0-30%, crossfade 28-40%, CTA from 35%
  const stackOpacity = interpolate(frame / dur, [0, 0.28, 0.38], [1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ctaOpacity = interpolate(frame / dur, [0.32, 0.42], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // CTA background photo zoom
  const bgZoom = interpolate(frame / dur, [0.5, 1], [1.05, 1.18], { extrapolateRight: "clamp" });

  // CTA element timing (relative to CTA becoming visible)
  const ctaFrame = Math.max(0, frame - dur * 0.34);
  const lineIn = spring({ frame: ctaFrame - 2, fps, config: { damping: 15, stiffness: 100 } });
  const titleIn = spring({ frame: ctaFrame - 5, fps, config: { damping: 12, stiffness: 75 } });
  const subIn = spring({ frame: ctaFrame - 10, fps, config: { damping: 14, stiffness: 80 } });
  const btnIn = spring({ frame: ctaFrame - 16, fps, config: { damping: 10, stiffness: 65 } });
  const urlIn = interpolate(ctaFrame, [20, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const handleIn = interpolate(ctaFrame, [26, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pulse = ctaFrame > 28 ? 1 + Math.sin((ctaFrame - 28) * 0.06) * 0.015 : 1;

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {/* CTA background photo — always present, fades in */}
      <div style={{ opacity: ctaOpacity }}>
        <Img src={staticFile("photos/warbler_a.jpg")} style={{
          position: "absolute", width: "100%", height: "100%",
          objectFit: "cover", objectPosition: "center center",
          transform: `scale(${bgZoom})`, transformOrigin: "center center",
          filter: "brightness(0.2) saturate(0.7)",
        }} />
        <div style={{
          position: "absolute", width: "100%", height: "100%",
          background: "linear-gradient(rgba(26,26,24,0.3) 0%, rgba(26,26,24,0.8) 45%, rgba(26,26,24,0.95) 100%)",
        }} />
      </div>

      {/* Ink background for service stack — fades with stack */}
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #222220 0%, ${colors.ink} 70%)`,
        opacity: stackOpacity,
      }} />

      {/* SERVICE STACK */}
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
        opacity: stackOpacity,
      }}>
        <div style={{ textAlign: "center", marginTop: -100 }}>
          {services.map((svc, i) => {
            const s = spring({ frame: frame - (1 + i * 1.4), fps, config: { damping: 14, stiffness: 130 } });
            return (
              <div key={svc} style={{
                fontFamily: fonts.display, fontSize: 40, fontWeight: 700,
                color: i % 2 === 0 ? colors.gold : colors.paper,
                letterSpacing: "0.15em", lineHeight: 1.9,
                opacity: Math.min(s * 2.5, 1), transform: `translateY(${(1 - s) * 12}px)`,
              }}>{svc}</div>
            );
          })}
        </div>

        {(() => { const s = spring({ frame: frame - 16, fps, config: { damping: 15, stiffness: 90 } });
          return <div style={{ width: s * 250, height: 3, backgroundColor: colors.gold, marginTop: 30 }} />;
        })()}

        {(() => { const s = spring({ frame: frame - 19, fps, config: { damping: 12, stiffness: 80 } });
          return <div style={{ fontFamily: fonts.serif, fontSize: 64, fontWeight: 300, color: colors.paper,
            marginTop: 20, opacity: Math.min(s*2,1), transform: `translateY(${(1-s)*10}px)` }}>One creative partner.</div>;
        })()}
      </div>

      {/* CTA CONTENT */}
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
        opacity: ctaOpacity,
      }}>
        <div style={{ width: lineIn * 200, height: 2, backgroundColor: colors.gold, marginBottom: 30 }} />

        <div style={{
          fontFamily: fonts.serif, fontSize: 60, fontWeight: 300,
          color: colors.paper, textAlign: "center", lineHeight: 1.3,
          opacity: Math.min(titleIn * 2, 1),
          transform: `translateY(${(1 - titleIn) * 18}px)`,
          textShadow: "0 2px 25px rgba(0,0,0,0.6)",
        }}>
          See the full scope.
        </div>

        <div style={{
          fontFamily: fonts.sans, fontSize: 24, fontWeight: 400,
          color: colors.lightStone, textAlign: "center", marginTop: 16,
          opacity: Math.min(subIn * 2, 1),
          transform: `translateY(${(1 - subIn) * 12}px)`,
          textShadow: "0 1px 15px rgba(0,0,0,0.5)",
        }}>
          4 projects. 42 pages. 12 months of creative partnership.
        </div>

        <div style={{
          marginTop: 45,
          opacity: Math.min(btnIn * 2, 1),
          transform: `translateY(${(1 - btnIn) * 15}px) scale(${pulse})`,
        }}>
          <div style={{
            fontFamily: fonts.display, fontSize: 32, fontWeight: 700,
            color: colors.ink, letterSpacing: "0.1em",
            backgroundColor: colors.gold,
            borderRadius: 8, padding: "20px 55px",
            display: "inline-block",
            boxShadow: "0 8px 35px rgba(201,169,110,0.35)",
          }}>
            VIEW CASE STUDY
          </div>
        </div>

        <div style={{
          fontFamily: fonts.sans, fontSize: 23, color: colors.gold,
          marginTop: 26, opacity: urlIn, letterSpacing: "0.02em",
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>
          mattanthonyphoto.com/balmoral-construction
        </div>

        <div style={{
          fontFamily: fonts.sans, fontSize: 25, fontWeight: 500,
          color: colors.stone, marginTop: 18, opacity: handleIn,
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>
          @balmoralconstruction &nbsp;&times;&nbsp; @mattanthonyphoto
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ===== MAIN COMPOSITION =====
export const BalmoralReel: React.FC = () => {
  const { fps } = useVideoConfig();
  const BEAT = Math.round(0.625 * fps);
  const FLASH = 3;

  const HOOK_DUR = BEAT * 3;
  const SLIDE_DUR = BEAT * 2;
  const WEB_DUR = BEAT * 7;
  const usedBeats = 3 + (7 * 2) + 7; // 24 beats
  // Gallery + web = 24 beats = ~15s. Remaining for end section to hit 26s:
  const END_SECTION_DUR = (TOTAL_SECONDS * fps) - (usedBeats * BEAT); // fills to 26s

  let f = 0;

  const renderSlide = (slide: Slide, idx: number) => {
    const start = f;
    f += SLIDE_DUR;
    const C = slide.layout === "fullscreen" ? Fullscreen
      : slide.layout === "stacked-pair" ? StackedPair
      : slide.layout === "big-small" ? BigSmall
      : HorizontalFloat;
    return (
      <React.Fragment key={idx}>
        <Sequence from={start} durationInFrames={SLIDE_DUR}><C slide={slide} dur={SLIDE_DUR} /></Sequence>
        <Sequence from={start + SLIDE_DUR - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      </React.Fragment>
    );
  };

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Audio
        src={staticFile("music.mp3")}
        volume={(f) => {
          // Fade in over first 0.5s, full volume, fade out over last 2.5s
          const fadeIn = Math.min(f / (0.5 * 30), 1);
          const fadeOutStart = (TOTAL_SECONDS - 2.5) * 30;
          const fadeOut = f > fadeOutStart
            ? 1 - ((f - fadeOutStart) / (2.5 * 30))
            : 1;
          return 0.8 * fadeIn * Math.max(0, fadeOut);
        }}
      />

      {/* Hook */}
      <Sequence from={f} durationInFrames={HOOK_DUR}><Hook /></Sequence>
      <Sequence from={f + HOOK_DUR - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += HOOK_DUR; return null; })()}

      {/* Gallery */}
      {slides.map((slide, i) => renderSlide(slide, i))}

      {/* Website */}
      <Sequence from={f} durationInFrames={WEB_DUR}><WebsiteScroll dur={WEB_DUR} /></Sequence>
      {(() => { f += WEB_DUR; return null; })()}

      {/* End section — service stack crossfades into CTA */}
      <Sequence from={f} durationInFrames={END_SECTION_DUR}><EndSection dur={END_SECTION_DUR} /></Sequence>

      {/* Global overlays */}
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><FilmGrain /></Sequence>
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><ColorGrade /></Sequence>
    </AbsoluteFill>
  );
};
