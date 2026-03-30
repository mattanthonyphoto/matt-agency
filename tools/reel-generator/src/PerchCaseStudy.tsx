import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, spring,
  useCurrentFrame, useVideoConfig, interpolate, staticFile,
} from "remotion";
import { colors, fonts } from "./brand";

const TOTAL_SECONDS = 50;
const XFADE = 10;

// ── SHARED ──────────────────────────────────────────────

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{
      position: "absolute", inset: 0,
      opacity: 0.022, mixBlendMode: "overlay", pointerEvents: "none",
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' seed='${Math.floor(frame * 1.7)}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
      backgroundSize: "150px 150px",
    }} />
  );
};

const Vig: React.FC = () => (
  <div style={{
    position: "absolute", inset: 0, pointerEvents: "none",
    background: "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.45) 100%)",
  }} />
);

const env = (frame: number, dur: number, fadeIn = XFADE, fadeOut = XFADE) =>
  interpolate(frame, [0, fadeIn, dur - fadeOut, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

// ── 1. LETTERBOX REVEAL — cinematic bars open on twilight hero ──

const LetterboxReveal: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();

  // Bars start at 45% (almost closed), open to 0% over first 2s
  const barHeight = interpolate(frame, [0, 60], [45, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Photo brightens as bars open
  const brightness = interpolate(frame, [0, 10, 50], [0, 0.5, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Slow zoom out — starts tight, reveals context
  const zoom = interpolate(frame, [0, dur], [1.25, 1.05], { extrapolateRight: "clamp" });

  // Fade out at end
  const fadeOut = interpolate(frame, [dur - 5, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      <Img src={staticFile("photos/perch/twilight_hero.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center 38%",
        transform: `scale(${zoom})`, transformOrigin: "center center",
        filter: `brightness(${brightness})`,
        opacity: fadeOut,
      }} />
      {/* Gradient at bottom */}
      <div style={{
        position: "absolute", bottom: 0, width: "100%", height: "25%",
        background: "linear-gradient(transparent, rgba(0,0,0,0.5))",
        opacity: fadeOut * brightness,
      }} />
      {/* Top letterbox bar */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0,
        height: `${barHeight}%`, backgroundColor: "#000",
        transition: "none",
      }} />
      {/* Bottom letterbox bar */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0,
        height: `${barHeight}%`, backgroundColor: "#000",
        transition: "none",
      }} />
    </AbsoluteFill>
  );
};

// ── 2. TITLE SLAM — fast, punchy ──

const TitleSlam: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lineIn = spring({ frame: frame - 2, fps, config: { damping: 12, stiffness: 130 } });
  const caseIn = spring({ frame: frame - 4, fps, config: { damping: 10, stiffness: 120 } });
  const titleIn = spring({ frame: frame - 6, fps, config: { damping: 10, stiffness: 100 } });
  const locIn = spring({ frame: frame - 12, fps, config: { damping: 14, stiffness: 90 } });
  const o = env(frame, dur, 3, XFADE);

  const titleScale = interpolate(titleIn, [0, 0.35, 0.65, 1], [0.5, 1.06, 0.98, 1]);

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={{
        width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center", opacity: o,
      }}>
        <div style={{
          width: lineIn * 70, height: 1,
          backgroundColor: colors.gold, opacity: 0.7, marginBottom: 30,
        }} />
        <div style={{
          fontFamily: fonts.display, fontSize: 15, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.5em",
          opacity: Math.min(caseIn * 2.5, 1), marginBottom: 12,
        }}>CASE STUDY</div>
        <div style={{
          fontFamily: fonts.serif, fontSize: 82, fontWeight: 300,
          color: colors.paper, letterSpacing: "0.08em",
          transform: `scale(${titleScale})`,
          opacity: Math.min(titleIn * 2.5, 1),
        }}>The Perch</div>
        <div style={{
          fontFamily: fonts.display, fontSize: 17, fontWeight: 600,
          color: colors.stone, letterSpacing: "0.35em", marginTop: 14,
          opacity: Math.min(locIn * 2, 1),
          transform: `translateY(${(1 - locIn) * 6}px)`,
        }}>SUNSHINE COAST, BC</div>
        <div style={{
          width: lineIn * 70, height: 1,
          backgroundColor: colors.gold, opacity: 0.7, marginTop: 30,
        }} />
      </div>
    </AbsoluteFill>
  );
};

// ── 3. THE SITE — aerial, narrative question ──

const TheSite: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, dur], [1.1, 1.0], { extrapolateRight: "clamp" });
  const o = env(frame, dur);

  const t1 = spring({ frame: frame - 14, fps, config: { damping: 25, stiffness: 35 } });
  const t2 = spring({ frame: frame - 30, fps, config: { damping: 25, stiffness: 35 } });
  const tOut = interpolate(frame, [dur - 14, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/perch/aerial.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center 40%",
        transform: `scale(${zoom})`, opacity: o,
      }} />
      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "55%",
        background: "linear-gradient(transparent, rgba(0,0,0,0.9))", opacity: o }} />

      <div style={{ position: "absolute", bottom: 200, width: "100%", padding: "0 55px" }}>
        <div style={{
          fontFamily: fonts.serif, fontSize: 40, fontWeight: 300,
          color: colors.paper, lineHeight: 1.4,
          textShadow: "0 2px 30px rgba(0,0,0,0.9)",
          opacity: Math.min(t1 * 2, 1) * tOut,
          transform: `translateY(${(1 - t1) * 14}px)`,
        }}>
          Granite shoreline.{"\n"}Old-growth canopy.{"\n"}Salish Sea below.
        </div>
        <div style={{
          fontFamily: fonts.serif, fontSize: 42, fontWeight: 300,
          color: colors.gold, fontStyle: "italic", marginTop: 16,
          textShadow: "0 2px 30px rgba(0,0,0,0.9)",
          opacity: Math.min(t2 * 2, 1) * tOut,
          transform: `translateY(${(1 - t2) * 12}px)`,
        }}>
          How do you build here{"\n"}without losing this?
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── 4. THE BRIEF — split text, high tension ──

const TheBrief: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, dur], [1.06, 1.0], { extrapolateRight: "clamp" });
  const o = env(frame, dur);

  const label = spring({ frame: frame - 5, fps, config: { damping: 16, stiffness: 80 } });
  const l1 = spring({ frame: frame - 10, fps, config: { damping: 18, stiffness: 55 } });
  const l2 = spring({ frame: frame - 20, fps, config: { damping: 18, stiffness: 55 } });
  const l3 = spring({ frame: frame - 32, fps, config: { damping: 20, stiffness: 45 } });
  const tOut = interpolate(frame, [dur - 12, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/perch/entry.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", transform: `scale(${zoom})`,
        filter: "brightness(0.22) saturate(0.5)",
        opacity: o,
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", padding: "0 58px", opacity: o,
      }}>
        <div style={{
          fontFamily: fonts.display, fontSize: 15, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.45em", marginBottom: 24,
          opacity: Math.min(label * 2.5, 1),
        }}>THE BRIEF</div>

        <div style={{
          fontFamily: fonts.serif, fontSize: 46, fontWeight: 300,
          color: colors.paper, lineHeight: 1.3,
          opacity: Math.min(l1 * 2, 1) * tOut,
          transform: `translateY(${(1 - l1) * 12}px)`,
          textShadow: "0 2px 20px rgba(0,0,0,0.7)",
        }}>
          Don't photograph{"\n"}the house.
        </div>

        <div style={{
          fontFamily: fonts.serif, fontSize: 46, fontWeight: 300,
          color: colors.gold, lineHeight: 1.3, fontStyle: "italic",
          marginTop: 8,
          opacity: Math.min(l2 * 2, 1) * tOut,
          transform: `translateY(${(1 - l2) * 12}px)`,
          textShadow: "0 2px 20px rgba(0,0,0,0.7)",
        }}>
          Photograph the feeling{"\n"}of arriving.
        </div>

        <div style={{
          width: 50, height: 1, backgroundColor: colors.gold,
          marginTop: 28, opacity: 0.5 * Math.min(l3 * 2, 1) * tOut,
        }} />

        <div style={{
          fontFamily: fonts.sans, fontSize: 19, fontWeight: 300,
          color: colors.stone, marginTop: 18, lineHeight: 1.6,
          opacity: Math.min(l3 * 2, 1) * tOut,
          transform: `translateY(${(1 - l3) * 8}px)`,
        }}>
          Charred cedar. Polished concrete.{"\n"}Glass dissolving into forest.
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── 5. HALLWAY REVEAL — the architectural moment ──

const HallwayReveal: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const zoom = interpolate(frame, [0, dur], [1.0, 1.08], { extrapolateRight: "clamp" });
  const o = env(frame, dur, 14, XFADE);

  const textIn = spring({ frame: frame - Math.round(dur * 0.35), fps, config: { damping: 30, stiffness: 30 } });
  const textOut = interpolate(frame, [dur - 14, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/perch/hallway.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center center",
        transform: `scale(${zoom})`,
        opacity: o,
      }} />

      {/* Centered text overlay */}
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", justifyContent: "center", alignItems: "center",
        opacity: Math.min(textIn * 2, 1) * textOut,
      }}>
        <div style={{
          fontFamily: fonts.serif, fontSize: 38, fontWeight: 300,
          color: colors.paper, textAlign: "center", fontStyle: "italic",
          textShadow: "0 2px 40px rgba(0,0,0,0.95), 0 0 80px rgba(0,0,0,0.6)",
          letterSpacing: "0.05em", lineHeight: 1.4,
          padding: "0 60px",
        }}>
          Where the corridor{"\n"}becomes the view.
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── 6. RAPID MONTAGE — speed ramp with rotation ──

const RapidMontage: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const photos = [
    "cantilever.jpg", "fireplace_wide.jpg", "rear.jpg",
    "kitchen.jpg", "ensuite.jpg", "side.jpg",
    "entry.jpg", "fireplace.jpg", "aerial.jpg",
  ];
  // Accelerating then decelerating: 9, 7, 6, 5, 4, 4, 5, 6, fill
  const timings = [9, 7, 6, 5, 4, 4, 5, 6, 0];
  let accumulated = 0;
  let currentIndex = 0;
  for (let i = 0; i < timings.length - 1; i++) {
    if (frame >= accumulated + timings[i]) {
      accumulated += timings[i];
      currentIndex = i + 1;
    } else break;
  }
  currentIndex = Math.min(currentIndex, photos.length - 1);
  const localFrame = frame - accumulated;

  // Alternating subtle rotations
  const rot = (currentIndex % 2 === 0 ? 0.8 : -0.8) * interpolate(localFrame, [0, 3], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Slam scale
  const slam = interpolate(localFrame, [0, 1, 3], [1.12, 0.98, 1.0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const o = env(frame, dur, 2, 2);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      <Img
        src={staticFile(`photos/perch/${photos[currentIndex]}`)}
        style={{
          position: "absolute", width: "100%", height: "100%",
          objectFit: "cover",
          transform: `scale(${slam}) rotate(${rot}deg)`,
          transformOrigin: "center center",
          opacity: o,
        }}
      />
    </AbsoluteFill>
  );
};

// ── 7. BLACK BREATH — pure black with pulsing gold line ──

const BlackBreath: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();

  // Gold line pulses like a heartbeat
  const pulse = Math.sin(frame * 0.15) * 0.3 + 0.5;
  const width = interpolate(frame, [0, 10, dur - 8, dur], [0, 40, 40, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <div style={{
        position: "absolute", top: "50%", left: "50%",
        transform: "translate(-50%, -50%)",
        width, height: 1,
        backgroundColor: colors.gold, opacity: pulse,
      }} />
    </AbsoluteFill>
  );
};

// ── 8. HERO HOLD — the payoff, long breathe ──

const HeroHold: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const zoom = interpolate(frame, [0, dur], [1.1, 1.0], { extrapolateRight: "clamp" });

  // Slow reveal from black
  const fadeIn = interpolate(frame, [0, 25], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [dur - XFADE, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Text late
  const textIn = spring({ frame: frame - Math.round(dur * 0.5), fps, config: { damping: 32, stiffness: 25 } });
  const textOut = interpolate(frame, [dur - 18, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      <Img src={staticFile("photos/perch/twilight_hero.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center 38%",
        transform: `scale(${zoom})`,
        opacity: Math.min(fadeIn, fadeOut),
      }} />
      <div style={{
        position: "absolute", bottom: 0, width: "100%", height: "35%",
        background: "linear-gradient(transparent, rgba(0,0,0,0.65))",
        opacity: Math.min(fadeIn, fadeOut),
      }} />

      <div style={{
        position: "absolute", bottom: 240, width: "100%", textAlign: "center",
        opacity: Math.min(textIn * 2, 1) * textOut,
        transform: `translateY(${(1 - textIn) * 10}px)`,
      }}>
        <div style={{
          fontFamily: fonts.serif, fontSize: 34, fontWeight: 300,
          color: colors.paper, fontStyle: "italic",
          textShadow: "0 2px 40px rgba(0,0,0,0.95)",
          letterSpacing: "0.04em",
        }}>
          This is the frame{"\n"}that sells the next project.
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── 9. STACKED — exterior/interior ──

const Stacked: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s1 = spring({ frame: frame - 5, fps, config: { damping: 24, stiffness: 36 } });
  const s2 = spring({ frame: frame - 16, fps, config: { damping: 24, stiffness: 36 } });
  const lineIn = spring({ frame: frame - 25, fps, config: { damping: 26, stiffness: 40 } });
  const z1 = interpolate(frame, [0, dur], [1.0, 1.04], { extrapolateRight: "clamp" });
  const z2 = interpolate(frame, [0, dur], [1.04, 1.0], { extrapolateRight: "clamp" });
  const o = env(frame, dur);
  const shadow = "0 18px 55px rgba(0,0,0,0.55)";
  const h1 = Math.sin(frame * 0.035) * 1.2;
  const h2 = Math.cos(frame * 0.035) * 1.2;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={{ position: "absolute", inset: 0,
        background: `radial-gradient(ellipse at center, #1d1d1b 0%, ${colors.ink} 75%)` }} />

      <div style={{
        position: "absolute", top: "10%", left: "5%", right: "12%",
        transform: `translateY(${(1 - s1) * -50 + (s1 > 0.95 ? h1 : 0)}px) rotate(${(1 - s1) * -0.8}deg)`,
        borderRadius: 3, overflow: "hidden", boxShadow: shadow,
        opacity: Math.min(s1 * 2, 1) * o,
      }}>
        <Img src={staticFile("photos/perch/side.jpg")} style={{
          width: "100%", display: "block", transform: `scale(${z1})`,
        }} />
      </div>

      <div style={{
        position: "absolute", top: "49%", left: "8%",
        width: `${lineIn * 84}%`, height: 1,
        backgroundColor: colors.gold, opacity: 0.35 * o,
      }} />

      <div style={{
        position: "absolute", top: "52%", left: "12%", right: "5%",
        transform: `translateY(${(1 - s2) * 50 + (s2 > 0.95 ? h2 : 0)}px) rotate(${(1 - s2) * 0.6}deg)`,
        borderRadius: 3, overflow: "hidden", boxShadow: shadow,
        opacity: Math.min(s2 * 2, 1) * o,
      }}>
        <Img src={staticFile("photos/perch/fireplace_wide.jpg")} style={{
          width: "100%", display: "block", transform: `scale(${z2})`,
        }} />
      </div>

      <div style={{
        position: "absolute", bottom: 95, width: "100%", textAlign: "center",
        fontFamily: fonts.display, fontSize: 14, fontWeight: 600,
        color: colors.gold, letterSpacing: "0.35em",
        opacity: Math.min(lineIn * 2, 1) * o,
      }}>
        OUTSIDE IN &nbsp;&middot;&nbsp; INSIDE OUT
      </div>
    </AbsoluteFill>
  );
};

// ── 10. STATS OVER PHOTOS — numbers floating on images ──

const StatsOverPhotos: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const stats = [
    { num: "26", label: "FRAMES", photo: "rear.jpg" },
    { num: "1", label: "DAY", photo: "cantilever.jpg" },
    { num: "6", label: "PERSPECTIVES", photo: "ensuite.jpg" },
  ];

  const segDur = Math.floor(dur / 3);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      {stats.map((stat, i) => {
        const segStart = i * segDur;
        const localFrame = frame - segStart;
        const isActive = localFrame >= 0 && localFrame < segDur;
        if (!isActive) return null;

        const zoom = interpolate(localFrame, [0, segDur], [1.08, 1.0], { extrapolateRight: "clamp" });
        const photoO = interpolate(localFrame, [0, 6, segDur - 4, segDur], [0, 0.45, 0.45, 0], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });

        const s = spring({ frame: localFrame - 4, fps, config: { damping: 12, stiffness: 80 } });
        const numScale = interpolate(s, [0, 0.35, 0.65, 1], [0.4, 1.1, 0.97, 1]);
        const textO = interpolate(localFrame, [0, 6, segDur - 6, segDur], [0, 1, 1, 0], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });

        return (
          <AbsoluteFill key={stat.label}>
            <Img src={staticFile(`photos/perch/${stat.photo}`)} style={{
              position: "absolute", width: "100%", height: "100%",
              objectFit: "cover", transform: `scale(${zoom})`,
              filter: "brightness(0.3) saturate(0.4)",
              opacity: photoO,
            }} />
            <div style={{
              position: "absolute", inset: 0,
              display: "flex", flexDirection: "column",
              justifyContent: "center", alignItems: "center",
              opacity: textO,
            }}>
              <div style={{
                fontFamily: fonts.serif, fontSize: 120, fontWeight: 300,
                color: colors.paper, letterSpacing: "0.03em", lineHeight: 1,
                transform: `scale(${numScale})`,
                textShadow: "0 4px 40px rgba(0,0,0,0.8)",
              }}>{stat.num}</div>
              <div style={{
                fontFamily: fonts.display, fontSize: 18, fontWeight: 700,
                color: colors.gold, letterSpacing: "0.4em", marginTop: 8,
                textShadow: "0 2px 20px rgba(0,0,0,0.8)",
              }}>{stat.label}</div>
            </div>
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};

// ── 11. CLIENT VOICE — word-by-word reveal ──

const ClientVoice: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, dur], [1.04, 1.0], { extrapolateRight: "clamp" });
  const o = env(frame, dur, 16, XFADE);

  // Word-by-word quote
  const words = ["His", "creative", "eye", "brought", "our", "project", "to", "life."];
  const wordDelay = 4; // frames between each word
  const startFrame = 14;

  const attrIn = spring({ frame: frame - startFrame - words.length * wordDelay - 8, fps, config: { damping: 25, stiffness: 32 } });
  const tOut = interpolate(frame, [dur - 14, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/perch/fireplace.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", transform: `scale(${zoom})`,
        filter: "brightness(0.13) saturate(0.35)",
        opacity: o,
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
        padding: "0 55px", opacity: o,
      }}>
        {/* Quote mark */}
        <div style={{
          fontFamily: fonts.serif, fontSize: 90, fontWeight: 300,
          color: colors.gold, opacity: 0.25,
          lineHeight: 0.5, marginBottom: 24,
        }}>"</div>

        {/* Word-by-word */}
        <div style={{
          fontFamily: fonts.serif, fontSize: 36, fontWeight: 300,
          color: colors.paper, textAlign: "center",
          lineHeight: 1.6, fontStyle: "italic",
          textShadow: "0 2px 25px rgba(0,0,0,0.8)",
        }}>
          {words.map((word, i) => {
            const wIn = spring({
              frame: frame - startFrame - i * wordDelay, fps,
              config: { damping: 18, stiffness: 60 },
            });
            return (
              <span key={i} style={{
                opacity: Math.min(wIn * 2.5, 1) * tOut,
                display: "inline-block",
                transform: `translateY(${(1 - wIn) * 8}px)`,
                marginRight: 10,
              }}>
                {word}
              </span>
            );
          })}
        </div>

        {/* Attribution */}
        <div style={{
          width: 45, height: 1, backgroundColor: colors.gold,
          marginTop: 30, marginBottom: 16,
          opacity: 0.5 * Math.min(attrIn * 2, 1) * tOut,
        }} />
        <div style={{
          fontFamily: fonts.display, fontSize: 14, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.35em",
          opacity: Math.min(attrIn * 2, 1) * tOut,
        }}>KYLE PAISLEY</div>
        <div style={{
          fontFamily: fonts.sans, fontSize: 16, fontWeight: 400,
          color: colors.stone, marginTop: 4,
          opacity: Math.min(attrIn * 2, 1) * tOut,
        }}>Summerhill Fine Homes</div>
      </div>
    </AbsoluteFill>
  );
};

// ── 12. CLOSING — direct, earned ──

const Closing: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bgZoom = interpolate(frame, [0, dur], [1.0, 1.05], { extrapolateRight: "clamp" });
  const bgIn = interpolate(frame, [0, 22], [0, 0.16], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const lineIn = spring({ frame: frame - 5, fps, config: { damping: 16, stiffness: 80 } });
  const h1 = spring({ frame: frame - 8, fps, config: { damping: 14, stiffness: 65 } });
  const h2 = spring({ frame: frame - 16, fps, config: { damping: 16, stiffness: 55 } });
  const nameIn = spring({ frame: frame - 24, fps, config: { damping: 20, stiffness: 45 } });
  const urlIn = spring({ frame: frame - 36, fps, config: { damping: 20, stiffness: 45 } });

  const h1Scale = interpolate(h1, [0, 0.35, 0.65, 1], [0.7, 1.04, 0.99, 1]);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/perch/twilight_wide.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", transform: `scale(${bgZoom})`,
        filter: "brightness(0.08) saturate(0.35) blur(1.5px)",
        opacity: bgIn,
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
      }}>
        <div style={{
          width: lineIn * 55, height: 1,
          backgroundColor: colors.gold, opacity: 0.6, marginBottom: 28,
        }} />

        <div style={{
          fontFamily: fonts.serif, fontSize: 44, fontWeight: 300,
          color: colors.paper, textAlign: "center",
          opacity: Math.min(h1 * 2.5, 1),
          transform: `scale(${h1Scale})`,
        }}>
          Book the shoot.
        </div>
        <div style={{
          fontFamily: fonts.serif, fontSize: 44, fontWeight: 300,
          color: colors.gold, textAlign: "center", fontStyle: "italic",
          marginTop: 4,
          opacity: Math.min(h2 * 2, 1),
          transform: `translateY(${(1 - h2) * 10}px)`,
        }}>
          Build the brand.
        </div>

        <div style={{
          width: lineIn * 55, height: 1,
          backgroundColor: colors.gold, opacity: 0.6, marginTop: 28, marginBottom: 28,
        }} />

        <div style={{
          fontFamily: fonts.display, fontSize: 13, fontWeight: 700,
          color: colors.stone, letterSpacing: "0.4em",
          opacity: Math.min(nameIn * 2, 1),
        }}>PHOTOGRAPHED BY</div>

        <div style={{
          fontFamily: fonts.serif, fontSize: 42, fontWeight: 300,
          color: colors.paper, marginTop: 6, letterSpacing: "0.06em",
          opacity: Math.min(nameIn * 2, 1),
          transform: `translateY(${(1 - nameIn) * 6}px)`,
        }}>Matt Anthony</div>

        <div style={{
          fontFamily: fonts.sans, fontSize: 18, color: colors.lightStone,
          marginTop: 18, opacity: Math.min(urlIn * 2, 1),
        }}>mattanthonyphoto.com</div>
        <div style={{
          fontFamily: fonts.sans, fontSize: 16, fontWeight: 500,
          color: colors.stone, marginTop: 6, opacity: Math.min(urlIn * 2, 1),
        }}>@mattanthonyphoto</div>
      </div>
    </AbsoluteFill>
  );
};

// ── MAIN COMPOSITION ────────────────────────────────────

export const PerchCaseStudy: React.FC = () => {
  const { fps } = useVideoConfig();
  const S = fps;

  const T1 = Math.round(S * 4);     // letterbox reveal
  const T2 = Math.round(S * 3);     // title slam
  const T3 = Math.round(S * 6.5);   // the site
  const T4 = Math.round(S * 5.5);   // the brief
  const T5 = Math.round(S * 3.5);   // hallway reveal
  const T6 = Math.round(S * 3);     // rapid montage
  const T7 = Math.round(S * 1.5);   // black breath
  const T8 = Math.round(S * 6);     // hero hold
  const T9 = Math.round(S * 4.5);   // stacked
  const T10 = Math.round(S * 4);    // stats over photos
  const T11 = Math.round(S * 6);    // client voice

  const used = T1 + T2 + T3 + T4 + T5 + T6 + T7 + T8 + T9 + T10 + T11 - (10 * XFADE);
  const T12 = (TOTAL_SECONDS * fps) - used;

  let f = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Audio
        src={staticFile("perch_music2.mp3")}
        volume={(fr) => {
          // Music delayed 1.5s, builds slowly
          const fadeIn = interpolate(fr, [fps * 1.5, fps * 5], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const fadeOutStart = (TOTAL_SECONDS - 4.5) * fps;
          const fadeOut = fr > fadeOutStart ? 1 - ((fr - fadeOutStart) / (4.5 * fps)) : 1;
          return 0.55 * fadeIn * Math.max(0, fadeOut);
        }}
      />

      {/* 1. LETTERBOX REVEAL */}
      <Sequence from={f} durationInFrames={T1}><LetterboxReveal dur={T1} /></Sequence>
      {(() => { f += T1 - XFADE; return null; })()}

      {/* 2. TITLE SLAM */}
      <Sequence from={f} durationInFrames={T2}><TitleSlam dur={T2} /></Sequence>
      {(() => { f += T2 - XFADE; return null; })()}

      {/* 3. THE SITE */}
      <Sequence from={f} durationInFrames={T3}><TheSite dur={T3} /></Sequence>
      {(() => { f += T3 - XFADE; return null; })()}

      {/* 4. THE BRIEF */}
      <Sequence from={f} durationInFrames={T4}><TheBrief dur={T4} /></Sequence>
      {(() => { f += T4 - XFADE; return null; })()}

      {/* 5. HALLWAY REVEAL */}
      <Sequence from={f} durationInFrames={T5}><HallwayReveal dur={T5} /></Sequence>
      {(() => { f += T5 - XFADE; return null; })()}

      {/* 6. RAPID MONTAGE */}
      <Sequence from={f} durationInFrames={T6}><RapidMontage dur={T6} /></Sequence>
      {(() => { f += T6 - XFADE; return null; })()}

      {/* 7. BLACK BREATH */}
      <Sequence from={f} durationInFrames={T7}><BlackBreath dur={T7} /></Sequence>
      {(() => { f += T7 - XFADE; return null; })()}

      {/* 8. HERO HOLD */}
      <Sequence from={f} durationInFrames={T8}><HeroHold dur={T8} /></Sequence>
      {(() => { f += T8 - XFADE; return null; })()}

      {/* 9. STACKED */}
      <Sequence from={f} durationInFrames={T9}><Stacked dur={T9} /></Sequence>
      {(() => { f += T9 - XFADE; return null; })()}

      {/* 10. STATS OVER PHOTOS */}
      <Sequence from={f} durationInFrames={T10}><StatsOverPhotos dur={T10} /></Sequence>
      {(() => { f += T10 - XFADE; return null; })()}

      {/* 11. CLIENT VOICE */}
      <Sequence from={f} durationInFrames={T11}><ClientVoice dur={T11} /></Sequence>
      {(() => { f += T11 - XFADE; return null; })()}

      {/* 12. CLOSING */}
      <Sequence from={f} durationInFrames={T12}><Closing dur={T12} /></Sequence>

      {/* Global overlays */}
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><Grain /></Sequence>
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><Vig /></Sequence>
    </AbsoluteFill>
  );
};
