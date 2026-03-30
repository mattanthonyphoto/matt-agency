import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, Video, spring,
  useCurrentFrame, useVideoConfig, interpolate, staticFile,
} from "remotion";
import { colors, fonts } from "./brand";

const TOTAL_SECONDS = 50;
const XFADE = 12;

// ── SHARED ──────────────────────────────────────────────

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{
      position: "absolute", inset: 0,
      opacity: 0.02, mixBlendMode: "overlay", pointerEvents: "none",
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

const env = (frame: number, dur: number, fi = XFADE, fo = XFADE) =>
  interpolate(frame, [0, fi, dur - fo, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

// ── CINEMATIC VIDEO CLIP — with slow-mo option ──

const CineVideo: React.FC<{
  src: string;
  dur: number;
  playbackRate?: number;
  startFrom?: number;
  objectPos?: string;
  fadeIn?: number;
  fadeOut?: number;
}> = ({ src, dur, playbackRate = 0.5, startFrom = 0, objectPos = "center center", fadeIn = XFADE, fadeOut = XFADE }) => {
  const frame = useCurrentFrame();
  const o = env(frame, dur, fadeIn, fadeOut);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      <Video
        src={staticFile(src)}
        startFrom={startFrom}
        playbackRate={playbackRate}
        style={{
          position: "absolute", width: "100%", height: "100%",
          objectFit: "cover", objectPosition: objectPos,
          opacity: o,
        }}
        volume={0}
      />
    </AbsoluteFill>
  );
};

// ── CINEMATIC PHOTO ──

const CinePhoto: React.FC<{
  photo: string;
  dur: number;
  zoomDir?: "in" | "out";
  objectPos?: string;
}> = ({ photo, dur, zoomDir = "in", objectPos = "center center" }) => {
  const frame = useCurrentFrame();
  const zoom = zoomDir === "in"
    ? interpolate(frame, [0, dur], [1.0, 1.07], { extrapolateRight: "clamp" })
    : interpolate(frame, [0, dur], [1.07, 1.0], { extrapolateRight: "clamp" });
  const o = env(frame, dur);

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img src={staticFile(`photos/perch/${photo}`)} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: objectPos,
        transform: `scale(${zoom})`, opacity: o,
      }} />
    </AbsoluteFill>
  );
};

// ── TEXT OVERLAY ──

const TextOverlay: React.FC<{
  text: string;
  subtext?: string;
  position?: "bottom" | "center";
  delay?: number;
  dur: number;
  lineAbove?: boolean;
}> = ({ text, subtext, position = "bottom", delay = 15, dur, lineAbove = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lineIn = spring({ frame: frame - delay + 5, fps, config: { damping: 28, stiffness: 38 } });
  const textIn = spring({ frame: frame - delay, fps, config: { damping: 26, stiffness: 35 } });
  const subIn = spring({ frame: frame - delay - 10, fps, config: { damping: 26, stiffness: 35 } });
  const fadeOut = interpolate(frame, [dur - 14, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const posStyle = position === "center"
    ? { justifyContent: "center" as const }
    : { justifyContent: "flex-end" as const, paddingBottom: 260 };

  return (
    <AbsoluteFill style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      pointerEvents: "none", ...posStyle,
    }}>
      {lineAbove && (
        <div style={{
          width: lineIn * 50, height: 1,
          backgroundColor: colors.gold, opacity: 0.5 * fadeOut, marginBottom: 16,
        }} />
      )}
      <div style={{
        fontFamily: fonts.serif, fontSize: 38, fontWeight: 300,
        color: colors.paper, textAlign: "center",
        letterSpacing: "0.04em", lineHeight: 1.45,
        opacity: Math.min(textIn * 2, 1) * fadeOut,
        transform: `translateY(${(1 - textIn) * 12}px)`,
        textShadow: "0 2px 35px rgba(0,0,0,0.95), 0 0 60px rgba(0,0,0,0.5)",
        padding: "0 55px",
      }}>
        {text}
      </div>
      {subtext && (
        <div style={{
          fontFamily: fonts.display, fontSize: 16, fontWeight: 600,
          color: colors.gold, letterSpacing: "0.3em", marginTop: 12,
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

// ── TITLE CARD ──

const TitleCard: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lineIn = spring({ frame: frame - 3, fps, config: { damping: 12, stiffness: 120 } });
  const titleIn = spring({ frame: frame - 6, fps, config: { damping: 10, stiffness: 100 } });
  const locIn = spring({ frame: frame - 12, fps, config: { damping: 14, stiffness: 80 } });
  const o = env(frame, dur, 3, XFADE);
  const titleScale = interpolate(titleIn, [0, 0.35, 0.65, 1], [0.5, 1.05, 0.98, 1]);

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={{
        width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center", opacity: o,
      }}>
        <div style={{ width: lineIn * 70, height: 1, backgroundColor: colors.gold, opacity: 0.7, marginBottom: 30 }} />
        <div style={{
          fontFamily: fonts.serif, fontSize: 80, fontWeight: 300,
          color: colors.paper, letterSpacing: "0.08em",
          transform: `scale(${titleScale})`,
          opacity: Math.min(titleIn * 2.5, 1),
        }}>The Perch</div>
        <div style={{
          fontFamily: fonts.display, fontSize: 17, fontWeight: 600,
          color: colors.stone, letterSpacing: "0.35em", marginTop: 14,
          opacity: Math.min(locIn * 2, 1),
        }}>SUNSHINE COAST, BC</div>
        <div style={{ width: lineIn * 70, height: 1, backgroundColor: colors.gold, opacity: 0.7, marginTop: 30 }} />
      </div>
    </AbsoluteFill>
  );
};

// ── BLACK BREATH ──

const BlackBreath: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const pulse = Math.sin(frame * 0.15) * 0.3 + 0.5;
  const w = interpolate(frame, [0, 8, dur - 6, dur], [0, 35, 35, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <div style={{
        position: "absolute", top: "50%", left: "50%",
        transform: "translate(-50%, -50%)",
        width: w, height: 1, backgroundColor: colors.gold, opacity: pulse,
      }} />
    </AbsoluteFill>
  );
};

// ── STACKED PAIR ──

const StackedPair: React.FC<{ dur: number }> = ({ dur }) => {
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
      }}>OUTSIDE IN &nbsp;&middot;&nbsp; INSIDE OUT</div>
    </AbsoluteFill>
  );
};

// ── END CARD ──

const EndCard: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lineIn = spring({ frame: frame - 5, fps, config: { damping: 16, stiffness: 80 } });
  const h1 = spring({ frame: frame - 8, fps, config: { damping: 14, stiffness: 65 } });
  const h2 = spring({ frame: frame - 16, fps, config: { damping: 16, stiffness: 55 } });
  const nameIn = spring({ frame: frame - 24, fps, config: { damping: 20, stiffness: 45 } });
  const urlIn = spring({ frame: frame - 36, fps, config: { damping: 20, stiffness: 45 } });
  const h1Scale = interpolate(h1, [0, 0.35, 0.65, 1], [0.7, 1.04, 0.99, 1]);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      {/* Faint twilight bg */}
      <Img src={staticFile("photos/perch/twilight_wide.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover",
        filter: "brightness(0.08) saturate(0.3) blur(1.5px)",
        opacity: 0.15,
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
      }}>
        <div style={{ width: lineIn * 55, height: 1, backgroundColor: colors.gold, opacity: 0.6, marginBottom: 28 }} />
        <div style={{
          fontFamily: fonts.serif, fontSize: 44, fontWeight: 300,
          color: colors.paper, textAlign: "center",
          opacity: Math.min(h1 * 2.5, 1), transform: `scale(${h1Scale})`,
        }}>Book the shoot.</div>
        <div style={{
          fontFamily: fonts.serif, fontSize: 44, fontWeight: 300,
          color: colors.gold, textAlign: "center", fontStyle: "italic", marginTop: 4,
          opacity: Math.min(h2 * 2, 1), transform: `translateY(${(1 - h2) * 10}px)`,
        }}>Build the brand.</div>
        <div style={{ width: lineIn * 55, height: 1, backgroundColor: colors.gold, opacity: 0.6, marginTop: 28, marginBottom: 28 }} />
        <div style={{
          fontFamily: fonts.display, fontSize: 13, fontWeight: 700,
          color: colors.stone, letterSpacing: "0.4em", opacity: Math.min(nameIn * 2, 1),
        }}>PHOTOGRAPHED BY</div>
        <div style={{
          fontFamily: fonts.serif, fontSize: 42, fontWeight: 300,
          color: colors.paper, marginTop: 6, opacity: Math.min(nameIn * 2, 1),
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

export const PerchVideoReel: React.FC = () => {
  const { fps } = useVideoConfig();
  const S = fps;

  // Timeline — alternating video and stills for rhythm
  //
  // 1. DRONE WIDE slow-mo (4s) — aerial establishing, no text, scroll-stopper
  // 2. TITLE CARD (2.5s) — fast slam
  // 3. DRONE APPROACH slow-mo (5s) — driving in through forest to the house
  //    text: "Granite shoreline. Old-growth canopy."
  // 4. PHOTO: entry (3s) — "Charred cedar. Polished concrete."
  // 5. DRONE CANTILEVER slow-mo (5s) — orbiting the glass volume on granite
  //    text: "Built into the rock. Open to the water."
  // 6. GIMBAL FIREPLACE slow-mo (5s) — the hero interior, no text
  // 7. BLACK BREATH (1.5s)
  // 8. PHOTO: hallway (3.5s) — "Where the corridor becomes the view."
  // 9. GIMBAL KITCHEN slow-mo (4s) — evening light
  // 10. STACKED PAIR (4s) — exterior/interior
  // 11. DRONE TWILIGHT slow-mo (5.5s) — THE money shot, house lit up
  //     text late: "This is the frame that sells the next project."
  // 12. END CARD (remaining)

  const T1 = Math.round(S * 4);      // drone wide
  const T2 = Math.round(S * 2.5);    // title
  const T3 = Math.round(S * 5);      // drone approach
  const T4 = Math.round(S * 3);      // photo entry
  const T5 = Math.round(S * 5);      // drone cantilever
  const T6 = Math.round(S * 5);      // gimbal fireplace
  const T7 = Math.round(S * 1.5);    // black breath
  const T8 = Math.round(S * 3.5);    // photo hallway
  const T9 = Math.round(S * 4);      // gimbal kitchen
  const T10 = Math.round(S * 4);     // stacked pair
  const T11 = Math.round(S * 5.5);   // drone twilight

  const used = T1 + T2 + T3 + T4 + T5 + T6 + T7 + T8 + T9 + T10 + T11 - (10 * XFADE);
  const T12 = (TOTAL_SECONDS * fps) - used;

  let f = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Audio
        src={staticFile("perch_music2.mp3")}
        volume={(fr) => {
          const fadeIn = interpolate(fr, [fps * 1, fps * 4.5], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const fadeOutStart = (TOTAL_SECONDS - 4.5) * fps;
          const fadeOut = fr > fadeOutStart ? 1 - ((fr - fadeOutStart) / (4.5 * fps)) : 1;
          return 0.5 * fadeIn * Math.max(0, fadeOut);
        }}
      />

      {/* 1. DRONE WIDE — slow-mo aerial establishing */}
      <Sequence from={f} durationInFrames={T1}>
        <CineVideo src="video/perch/drone_wide.mp4" dur={T1} playbackRate={0.5} fadeIn={18} />
      </Sequence>
      {(() => { f += T1 - XFADE; return null; })()}

      {/* 2. TITLE */}
      <Sequence from={f} durationInFrames={T2}>
        <TitleCard dur={T2} />
      </Sequence>
      {(() => { f += T2 - XFADE; return null; })()}

      {/* 3. DRONE APPROACH — through forest to the house */}
      <Sequence from={f} durationInFrames={T3}>
        <CineVideo src="video/perch/drone_approach.mp4" dur={T3} playbackRate={0.6} />
        <TextOverlay
          text={"Granite shoreline.\nOld-growth canopy."}
          position="bottom" delay={20} dur={T3} lineAbove
        />
      </Sequence>
      {(() => { f += T3 - XFADE; return null; })()}

      {/* 4. PHOTO: entry — materials */}
      <Sequence from={f} durationInFrames={T4}>
        <CinePhoto photo="entry.jpg" dur={T4} zoomDir="in" />
        <TextOverlay
          text="Charred cedar. Polished concrete."
          subtext="MATERIAL PALETTE"
          position="bottom" delay={12} dur={T4}
        />
      </Sequence>
      {(() => { f += T4 - XFADE; return null; })()}

      {/* 5. DRONE CANTILEVER — orbiting the glass volume */}
      <Sequence from={f} durationInFrames={T5}>
        <CineVideo src="video/perch/drone_cantilever.mp4" dur={T5} playbackRate={0.5} />
        <TextOverlay
          text={"Built into the rock.\nOpen to the water."}
          position="bottom" delay={22} dur={T5} lineAbove
        />
      </Sequence>
      {(() => { f += T5 - XFADE; return null; })()}

      {/* 6. GIMBAL FIREPLACE — hero interior, slow-mo, no text */}
      <Sequence from={f} durationInFrames={T6}>
        <CineVideo src="video/perch/gimbal_fireplace.mp4" dur={T6} playbackRate={0.4} />
      </Sequence>
      {(() => { f += T6 - XFADE; return null; })()}

      {/* 7. BLACK BREATH */}
      <Sequence from={f} durationInFrames={T7}>
        <BlackBreath dur={T7} />
      </Sequence>
      {(() => { f += T7 - XFADE; return null; })()}

      {/* 8. PHOTO: hallway */}
      <Sequence from={f} durationInFrames={T8}>
        <CinePhoto photo="hallway.jpg" dur={T8} zoomDir="in" />
        <TextOverlay
          text="Where the corridor becomes the view."
          position="center" delay={14} dur={T8}
        />
      </Sequence>
      {(() => { f += T8 - XFADE; return null; })()}

      {/* 9. GIMBAL KITCHEN — evening light */}
      <Sequence from={f} durationInFrames={T9}>
        <CineVideo src="video/perch/gimbal_kitchen.mp4" dur={T9} playbackRate={0.5} />
      </Sequence>
      {(() => { f += T9 - XFADE; return null; })()}

      {/* 10. STACKED PAIR */}
      <Sequence from={f} durationInFrames={T10}>
        <StackedPair dur={T10} />
      </Sequence>
      {(() => { f += T10 - XFADE; return null; })()}

      {/* 11. DRONE TWILIGHT — the money shot */}
      <Sequence from={f} durationInFrames={T11}>
        <CineVideo src="video/perch/drone_twilight.mp4" dur={T11} playbackRate={0.4} fadeIn={18} fadeOut={16} />
        <TextOverlay
          text={"This is the frame\nthat sells the next project."}
          position="bottom" delay={Math.round(T11 * 0.45)} dur={T11} lineAbove
        />
      </Sequence>
      {(() => { f += T11 - XFADE; return null; })()}

      {/* 12. END CARD */}
      <Sequence from={f} durationInFrames={T12}>
        <EndCard dur={T12} />
      </Sequence>

      {/* Global overlays */}
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><Grain /></Sequence>
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><Vig /></Sequence>
    </AbsoluteFill>
  );
};
