import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, spring,
  useCurrentFrame, useVideoConfig, interpolate, staticFile,
} from "remotion";
import { colors, fonts } from "./brand";

const TOTAL_SECONDS = 40;
const CROSSFADE = 10; // frames of overlap between slides

// ===== FILM GRAIN =====
const FilmGrain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{
      position: "absolute", top: 0, left: 0, width: "100%", height: "100%",
      opacity: 0.025, mixBlendMode: "overlay", pointerEvents: "none",
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' seed='${Math.floor(frame * 1.7)}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
      backgroundSize: "150px 150px",
    }} />
  );
};

// ===== CINEMATIC VIGNETTE — dark edges =====
const Vignette: React.FC = () => (
  <div style={{
    position: "absolute", top: 0, left: 0, width: "100%", height: "100%",
    background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.35) 100%)",
    pointerEvents: "none",
  }} />
);

// ===== WARM COLOR GRADE =====
const ColorGrade: React.FC = () => (
  <div style={{
    position: "absolute", top: 0, left: 0, width: "100%", height: "100%",
    background: "linear-gradient(180deg, rgba(180,160,120,0.03) 0%, transparent 25%, transparent 75%, rgba(26,26,24,0.06) 100%)",
    pointerEvents: "none", mixBlendMode: "soft-light",
  }} />
);

// ===== CINEMATIC PHOTO — slow zoom with crossfade =====
const CinematicPhoto: React.FC<{
  photo: string;
  dur: number;
  zoomDir?: "in" | "out";
  objectPos?: string;
  fadeIn?: number;
  fadeOut?: number;
  driftDir?: "up" | "down" | "left" | "right";
}> = ({
  photo, dur, zoomDir = "in", objectPos = "center center",
  fadeIn = CROSSFADE, fadeOut = CROSSFADE, driftDir = "up",
}) => {
  const frame = useCurrentFrame();

  // Ultra-slow zoom
  const zoom = zoomDir === "in"
    ? interpolate(frame, [0, dur], [1.0, 1.07], { extrapolateRight: "clamp" })
    : interpolate(frame, [0, dur], [1.07, 1.0], { extrapolateRight: "clamp" });

  // Directional drift
  const driftX = (driftDir === "left" || driftDir === "right")
    ? interpolate(frame, [0, dur], [driftDir === "left" ? 0.4 : -0.4, driftDir === "left" ? -0.4 : 0.4], { extrapolateRight: "clamp" })
    : 0;
  const driftY = (driftDir === "up" || driftDir === "down")
    ? interpolate(frame, [0, dur], [driftDir === "up" ? 0.3 : -0.3, driftDir === "up" ? -0.3 : 0.3], { extrapolateRight: "clamp" })
    : 0;

  // Smooth crossfade
  const opacity = interpolate(frame,
    [0, fadeIn, dur - fadeOut, dur],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img src={staticFile(`photos/perch/${photo}`)} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: objectPos,
        transform: `scale(${zoom}) translate(${driftX}%, ${driftY}%)`,
        transformOrigin: "center center",
        opacity,
      }} />
    </AbsoluteFill>
  );
};

// ===== ARCHITECTURAL TEXT — minimal, editorial =====
const ArchText: React.FC<{
  text: string;
  subtext?: string;
  position?: "bottom" | "center" | "top";
  delay?: number;
  dur: number;
  lineAbove?: boolean;
}> = ({ text, subtext, position = "bottom", delay = 15, dur, lineAbove = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lineIn = spring({ frame: frame - delay + 5, fps, config: { damping: 30, stiffness: 35 } });
  const textIn = spring({ frame: frame - delay, fps, config: { damping: 28, stiffness: 35 } });
  const subIn = spring({ frame: frame - delay - 10, fps, config: { damping: 28, stiffness: 35 } });
  const fadeOut = interpolate(frame, [dur - 12, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const posStyle = position === "center"
    ? { justifyContent: "center" as const }
    : position === "top"
    ? { justifyContent: "flex-start" as const, paddingTop: 280 }
    : { justifyContent: "flex-end" as const, paddingBottom: 280 };

  return (
    <AbsoluteFill style={{
      display: "flex", flexDirection: "column",
      alignItems: "center",
      pointerEvents: "none",
      ...posStyle,
    }}>
      {lineAbove && (
        <div style={{
          width: lineIn * 60, height: 1,
          backgroundColor: colors.gold, opacity: 0.6 * fadeOut,
          marginBottom: 18,
        }} />
      )}
      <div style={{
        fontFamily: fonts.serif, fontSize: 40, fontWeight: 300,
        color: colors.paper, textAlign: "center",
        letterSpacing: "0.04em", lineHeight: 1.45,
        opacity: Math.min(textIn * 2, 1) * fadeOut,
        transform: `translateY(${(1 - textIn) * 12}px)`,
        textShadow: "0 2px 35px rgba(0,0,0,0.9), 0 1px 10px rgba(0,0,0,0.6)",
        padding: "0 65px",
      }}>
        {text}
      </div>
      {subtext && (
        <div style={{
          fontFamily: fonts.display, fontSize: 18, fontWeight: 600,
          color: colors.gold, textAlign: "center",
          letterSpacing: "0.22em", marginTop: 14,
          opacity: Math.min(subIn * 2, 1) * fadeOut,
          transform: `translateY(${(1 - subIn) * 8}px)`,
          textShadow: "0 1px 20px rgba(0,0,0,0.8)",
        }}>
          {subtext}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ===== STACKED PAIR — two photos, exterior/interior relationship =====
const StackedPair: React.FC<{
  photo1: string;
  photo2: string;
  dur: number;
}> = ({ photo1, photo2, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s1 = spring({ frame: frame - 3, fps, config: { damping: 25, stiffness: 40 } });
  const s2 = spring({ frame: frame - 14, fps, config: { damping: 25, stiffness: 40 } });
  const lineIn = spring({ frame: frame - 22, fps, config: { damping: 28, stiffness: 45 } });

  const z1 = interpolate(frame, [0, dur], [1.0, 1.04], { extrapolateRight: "clamp" });
  const z2 = interpolate(frame, [0, dur], [1.04, 1.0], { extrapolateRight: "clamp" });

  // Fade everything out at end for crossfade
  const fadeOut = interpolate(frame, [dur - CROSSFADE, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const shadow = "0 15px 50px rgba(0,0,0,0.6), 0 5px 20px rgba(0,0,0,0.4)";
  const h1 = Math.sin(frame * 0.04) * 1.5;
  const h2 = Math.cos(frame * 0.04) * 1.5;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink, overflow: "hidden" }}>
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #1e1e1c 0%, ${colors.ink} 75%)`,
      }} />

      {/* Top photo — exterior */}
      <div style={{
        position: "absolute", top: "12%", left: "5%", right: "10%",
        transform: `translateY(${(1 - s1) * -60 + (s1 > 0.95 ? h1 : 0)}px) rotate(${(1 - s1) * -1.2}deg)`,
        borderRadius: 4, overflow: "hidden", boxShadow: shadow,
        opacity: Math.min(s1 * 2.5, 1) * fadeOut,
      }}>
        <Img src={staticFile(`photos/perch/${photo1}`)} style={{
          width: "100%", display: "block",
          transform: `scale(${z1})`, transformOrigin: "center center",
        }} />
      </div>

      {/* Gold accent line */}
      <div style={{
        position: "absolute", top: "50%", left: "8%",
        width: `${lineIn * 84}%`, height: 1,
        backgroundColor: colors.gold, opacity: 0.5 * fadeOut,
      }} />

      {/* Bottom photo — interior */}
      <div style={{
        position: "absolute", top: "53%", left: "10%", right: "5%",
        transform: `translateY(${(1 - s2) * 60 + (s2 > 0.95 ? h2 : 0)}px) rotate(${(1 - s2) * 1}deg)`,
        borderRadius: 4, overflow: "hidden", boxShadow: shadow,
        opacity: Math.min(s2 * 2.5, 1) * fadeOut,
      }}>
        <Img src={staticFile(`photos/perch/${photo2}`)} style={{
          width: "100%", display: "block",
          transform: `scale(${z2})`, transformOrigin: "center center",
        }} />
      </div>
    </AbsoluteFill>
  );
};

// ===== TITLE CARD — with photo emerging from darkness =====
const TitleCard: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Background photo slowly emerges from black
  const bgOpacity = interpolate(frame, [30, dur - 10], [0, 0.12], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const bgZoom = interpolate(frame, [0, dur], [1.1, 1.0], { extrapolateRight: "clamp" });

  // Staggered text entries
  const lineIn = spring({ frame: frame - 18, fps, config: { damping: 32, stiffness: 30 } });
  const titleIn = spring({ frame: frame - 26, fps, config: { damping: 28, stiffness: 28 } });
  const locIn = spring({ frame: frame - 38, fps, config: { damping: 28, stiffness: 28 } });
  const creditIn = spring({ frame: frame - 48, fps, config: { damping: 28, stiffness: 28 } });

  const fadeOut = interpolate(frame, [dur - 18, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink, overflow: "hidden" }}>
      {/* Faint twilight photo emerging */}
      <Img src={staticFile("photos/perch/twilight_hero.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center 40%",
        transform: `scale(${bgZoom})`, transformOrigin: "center center",
        filter: "brightness(0.15) saturate(0.4) blur(3px)",
        opacity: bgOpacity * fadeOut,
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
      }}>
        {/* Top line */}
        <div style={{
          width: lineIn * 100, height: 1,
          backgroundColor: colors.gold, opacity: 0.7 * fadeOut,
          marginBottom: 40,
        }} />

        {/* Title */}
        <div style={{
          fontFamily: fonts.serif, fontSize: 76, fontWeight: 300,
          color: colors.paper, letterSpacing: "0.1em",
          opacity: Math.min(titleIn * 2, 1) * fadeOut,
          transform: `translateY(${(1 - titleIn) * 10}px)`,
        }}>
          The Perch
        </div>

        {/* Location */}
        <div style={{
          fontFamily: fonts.display, fontSize: 20, fontWeight: 600,
          color: colors.stone, letterSpacing: "0.3em",
          marginTop: 18,
          opacity: Math.min(locIn * 2, 1) * fadeOut,
          transform: `translateY(${(1 - locIn) * 8}px)`,
        }}>
          SUNSHINE COAST, BC
        </div>

        {/* Builder */}
        <div style={{
          fontFamily: fonts.sans, fontSize: 17, fontWeight: 400,
          color: colors.stone, letterSpacing: "0.1em",
          marginTop: 28, opacity: 0.5 * Math.min(creditIn * 2, 1) * fadeOut,
          transform: `translateY(${(1 - creditIn) * 6}px)`,
        }}>
          Summerhill Fine Homes
        </div>

        {/* Bottom line */}
        <div style={{
          width: lineIn * 100, height: 1,
          backgroundColor: colors.gold, opacity: 0.7 * fadeOut,
          marginTop: 40,
        }} />
      </div>
    </AbsoluteFill>
  );
};

// ===== MATERIAL DETAIL — single photo with material callout strip =====
const MaterialDetail: React.FC<{
  photo: string;
  materials: string[];
  dur: number;
  zoomDir?: "in" | "out";
  objectPos?: string;
}> = ({ photo, materials, dur, zoomDir = "in", objectPos = "center center" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const zoom = zoomDir === "in"
    ? interpolate(frame, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" })
    : interpolate(frame, [0, dur], [1.06, 1.0], { extrapolateRight: "clamp" });

  const photoIn = interpolate(frame, [0, CROSSFADE], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const photoOut = interpolate(frame, [dur - CROSSFADE, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img src={staticFile(`photos/perch/${photo}`)} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: objectPos,
        transform: `scale(${zoom})`, transformOrigin: "center center",
        opacity: Math.min(photoIn, photoOut),
      }} />
      {/* Dark gradient at bottom for text */}
      <div style={{
        position: "absolute", bottom: 0, width: "100%", height: "40%",
        background: "linear-gradient(transparent, rgba(0,0,0,0.85))",
        opacity: Math.min(photoIn, photoOut),
      }} />
      {/* Material callouts */}
      <div style={{
        position: "absolute", bottom: 200, width: "100%",
        display: "flex", justifyContent: "center", gap: 30,
      }}>
        {materials.map((mat, i) => {
          const s = spring({ frame: frame - 20 - i * 6, fps, config: { damping: 25, stiffness: 40 } });
          const fadeOut2 = interpolate(frame, [dur - 12, dur], [1, 0], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          return (
            <div key={mat} style={{
              fontFamily: fonts.display, fontSize: 16, fontWeight: 600,
              color: colors.gold, letterSpacing: "0.2em",
              opacity: Math.min(s * 2, 1) * fadeOut2,
              transform: `translateY(${(1 - s) * 8}px)`,
              textShadow: "0 1px 15px rgba(0,0,0,0.8)",
              padding: "6px 16px",
              borderBottom: `1px solid rgba(201,169,110,${0.3 * Math.min(s * 2, 1) * fadeOut2})`,
            }}>
              {mat}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ===== END CARD =====
const EndCard: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgZoom = interpolate(frame, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" });
  const bgIn = interpolate(frame, [0, 25], [0, 0.18], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const lineIn = spring({ frame: frame - 10, fps, config: { damping: 30, stiffness: 35 } });
  const labelIn = spring({ frame: frame - 16, fps, config: { damping: 28, stiffness: 30 } });
  const nameIn = spring({ frame: frame - 22, fps, config: { damping: 25, stiffness: 30 } });
  const urlIn = spring({ frame: frame - 34, fps, config: { damping: 25, stiffness: 30 } });
  const handleIn = spring({ frame: frame - 42, fps, config: { damping: 25, stiffness: 30 } });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile("photos/perch/twilight_wide.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center center",
        transform: `scale(${bgZoom})`, transformOrigin: "center center",
        filter: "brightness(0.1) saturate(0.4) blur(2px)",
        opacity: bgIn,
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
      }}>
        <div style={{
          width: lineIn * 70, height: 1,
          backgroundColor: colors.gold, opacity: 0.6,
          marginBottom: 32,
        }} />

        <div style={{
          fontFamily: fonts.display, fontSize: 16, fontWeight: 600,
          color: colors.stone, letterSpacing: "0.35em",
          opacity: Math.min(labelIn * 2, 1),
          transform: `translateY(${(1 - labelIn) * 8}px)`,
        }}>
          PHOTOGRAPHED BY
        </div>

        <div style={{
          fontFamily: fonts.serif, fontSize: 52, fontWeight: 300,
          color: colors.paper, marginTop: 10,
          letterSpacing: "0.07em",
          opacity: Math.min(nameIn * 2, 1),
          transform: `translateY(${(1 - nameIn) * 8}px)`,
        }}>
          Matt Anthony
        </div>

        <div style={{
          width: lineIn * 70, height: 1,
          backgroundColor: colors.gold, opacity: 0.6,
          marginTop: 32, marginBottom: 28,
        }} />

        <div style={{
          fontFamily: fonts.sans, fontSize: 21, color: colors.lightStone,
          letterSpacing: "0.05em",
          opacity: Math.min(urlIn * 2, 1),
          transform: `translateY(${(1 - urlIn) * 6}px)`,
        }}>
          mattanthonyphoto.com
        </div>

        <div style={{
          fontFamily: fonts.sans, fontSize: 19, fontWeight: 500,
          color: colors.stone, marginTop: 10,
          opacity: Math.min(handleIn * 2, 1),
          transform: `translateY(${(1 - handleIn) * 6}px)`,
        }}>
          @mattanthonyphoto
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ===== MAIN COMPOSITION =====
export const PerchReel: React.FC = () => {
  const { fps } = useVideoConfig();
  const SEC = fps;

  // Timeline (40 seconds total) — with crossfade overlaps:
  // Effective visual time per slide = dur - CROSSFADE (since they overlap)
  //
  // 1. Title card: 5s
  // 2. Aerial establishing: 4s
  // 3. Front entry + materials: 4s — material callouts
  // 4. Cantilever detail: 3.5s
  // 5. Rear glass walls: 3.5s — "Perched on granite"
  // 6. Stacked pair (rear + fireplace): 4s — exterior/interior relationship
  // 7. Hallway corridor: 3.5s — "Where landscape becomes interior"
  // 8. Kitchen: 3s
  // 9. Ensuite: 3s — "Every room faces the water"
  // 10. Twilight hero: 5s — the money shot, no text
  // 11. End card: remaining (~4s)

  const TITLE = Math.round(SEC * 5);
  const S1 = Math.round(SEC * 4);     // aerial
  const S2 = Math.round(SEC * 4);     // entry + materials
  const S3 = Math.round(SEC * 3.5);   // cantilever
  const S4 = Math.round(SEC * 3.5);   // rear
  const S5 = Math.round(SEC * 4);     // stacked pair
  const S6 = Math.round(SEC * 3.5);   // hallway
  const S7 = Math.round(SEC * 3);     // kitchen
  const S8 = Math.round(SEC * 3);     // ensuite
  const S9 = Math.round(SEC * 5);     // twilight hero

  // Crossfade: each slide starts CROSSFADE frames before the previous ends
  // So effective timeline = sum of durations - (N-1) * CROSSFADE for photo slides
  // Title has no crossfade in, but crossfades out into aerial
  const photoSlides = S1 + S2 + S3 + S4 + S5 + S6 + S7 + S8 + S9;
  const crossfadeSavings = 8 * CROSSFADE; // 8 overlaps between 9 photo slides
  const usedFrames = TITLE + photoSlides - crossfadeSavings;
  const END = (TOTAL_SECONDS * fps) - usedFrames;

  // Build timeline with crossfade overlaps
  let f = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Audio
        src={staticFile("perch_music.mp3")}
        volume={(fr) => {
          const fadeIn = Math.min(fr / (2.5 * fps), 1);
          const fadeOutStart = (TOTAL_SECONDS - 3.5) * fps;
          const fadeOut = fr > fadeOutStart ? 1 - ((fr - fadeOutStart) / (3.5 * fps)) : 1;
          return 0.55 * fadeIn * Math.max(0, fadeOut);
        }}
      />

      {/* 1. TITLE CARD — emerging from black, twilight photo behind */}
      <Sequence from={f} durationInFrames={TITLE}>
        <TitleCard dur={TITLE} />
      </Sequence>
      {(() => { f += TITLE - CROSSFADE; return null; })()}

      {/* 2. AERIAL — house nestled in old-growth on rocky shore */}
      <Sequence from={f} durationInFrames={S1}>
        <CinematicPhoto photo="aerial.jpg" dur={S1} zoomDir="out" objectPos="center 40%" driftDir="up" />
      </Sequence>
      {(() => { f += S1 - CROSSFADE; return null; })()}

      {/* 3. FRONT ENTRY — material palette callouts */}
      <Sequence from={f} durationInFrames={S2}>
        <MaterialDetail
          photo="entry.jpg"
          materials={["CHARRED CEDAR", "GRANITE", "FIREWOOD"]}
          dur={S2}
          zoomDir="in"
          objectPos="center center"
        />
      </Sequence>
      {(() => { f += S2 - CROSSFADE; return null; })()}

      {/* 4. CANTILEVER — pure architecture, no text */}
      <Sequence from={f} durationInFrames={S3}>
        <CinematicPhoto photo="cantilever.jpg" dur={S3} zoomDir="out" objectPos="center center" driftDir="right" />
      </Sequence>
      {(() => { f += S3 - CROSSFADE; return null; })()}

      {/* 5. REAR — glass walls, concrete, forest */}
      <Sequence from={f} durationInFrames={S4}>
        <CinematicPhoto photo="rear.jpg" dur={S4} zoomDir="in" objectPos="center 35%" driftDir="left" />
        <ArchText
          text="Perched on granite."
          subtext="GROUNDED IN FOREST"
          position="bottom"
          delay={16}
          dur={S4}
          lineAbove
        />
      </Sequence>
      {(() => { f += S4 - CROSSFADE; return null; })()}

      {/* 6. STACKED PAIR — exterior/interior relationship */}
      <Sequence from={f} durationInFrames={S5}>
        <StackedPair photo1="cantilever.jpg" photo2="fireplace.jpg" dur={S5} />
      </Sequence>
      {(() => { f += S5 - CROSSFADE; return null; })()}

      {/* 7. HALLWAY — glass corridor, polished concrete */}
      <Sequence from={f} durationInFrames={S6}>
        <CinematicPhoto photo="hallway.jpg" dur={S6} zoomDir="in" objectPos="center center" driftDir="down" fadeIn={15} />
        <ArchText
          text="Where landscape becomes interior."
          position="center"
          delay={18}
          dur={S6}
          lineAbove
        />
      </Sequence>
      {(() => { f += S6 - CROSSFADE; return null; })()}

      {/* 8. KITCHEN — glass wall, ocean */}
      <Sequence from={f} durationInFrames={S7}>
        <CinematicPhoto photo="kitchen.jpg" dur={S7} zoomDir="out" objectPos="center center" driftDir="right" />
      </Sequence>
      {(() => { f += S7 - CROSSFADE; return null; })()}

      {/* 9. ENSUITE — tub, ocean view */}
      <Sequence from={f} durationInFrames={S8}>
        <CinematicPhoto photo="ensuite.jpg" dur={S8} zoomDir="in" objectPos="center center" driftDir="up" />
        <ArchText
          text="Every room faces the water."
          position="bottom"
          delay={12}
          dur={S8}
          lineAbove
        />
      </Sequence>
      {(() => { f += S8 - CROSSFADE; return null; })()}

      {/* 10. TWILIGHT HERO — the money shot, let it breathe */}
      <Sequence from={f} durationInFrames={S9}>
        <CinematicPhoto
          photo="twilight_hero.jpg" dur={S9}
          zoomDir="out" objectPos="center 40%"
          driftDir="left"
          fadeIn={18} fadeOut={15}
        />
      </Sequence>
      {(() => { f += S9 - CROSSFADE; return null; })()}

      {/* 11. END CARD */}
      <Sequence from={f} durationInFrames={END}>
        <EndCard dur={END} />
      </Sequence>

      {/* Global overlays */}
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><FilmGrain /></Sequence>
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><Vignette /></Sequence>
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><ColorGrade /></Sequence>
    </AbsoluteFill>
  );
};
