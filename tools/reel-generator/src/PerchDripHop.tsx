import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence,
  useCurrentFrame, useVideoConfig, interpolate, staticFile, spring,
} from "remotion";
import { colors, fonts } from "./brand";

const TOTAL_SECONDS = 28;
const FPS = 30;
const TOTAL_FRAMES = TOTAL_SECONDS * FPS;

// ── FILM GRAIN ──
const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{
      position: "absolute", inset: 0,
      opacity: 0.025, mixBlendMode: "overlay", pointerEvents: "none",
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' seed='${Math.floor(frame * 1.7)}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
      backgroundSize: "150px 150px",
    }} />
  );
};

// ── FULLSCREEN PHOTO — hard cut, Ken Burns ──
const FullPhoto: React.FC<{
  photo: string;
  dur: number;
  startScale?: number;
  endScale?: number;
  panX?: number;
  panY?: number;
  objectPosition?: string;
  brightness?: number;
}> = ({
  photo, dur,
  startScale = 1.0, endScale = 1.08,
  panX = 0, panY = 0,
  objectPosition = "center center",
  brightness = 1,
}) => {
  const frame = useCurrentFrame();
  const t = frame / dur;

  const scale = interpolate(t, [0, 1], [startScale, endScale], { extrapolateRight: "clamp" });
  const tx = interpolate(t, [0, 1], [0, panX], { extrapolateRight: "clamp" });
  const ty = interpolate(t, [0, 1], [0, panY], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img
        src={staticFile(`photos/perch/${photo}`)}
        style={{
          position: "absolute", width: "100%", height: "100%",
          objectFit: "cover", objectPosition,
          transform: `scale(${scale}) translate(${tx}px, ${ty}px)`,
          transformOrigin: "center center",
          filter: brightness !== 1 ? `brightness(${brightness})` : undefined,
        }}
      />
    </AbsoluteFill>
  );
};

// ── LETTERBOX REVEAL — bars open to reveal photo ──
const LetterboxReveal: React.FC<{
  photo: string;
  dur: number;
  openSpeed?: number;
  panX?: number;
  objectPosition?: string;
}> = ({ photo, dur, openSpeed = 45, panX = -8, objectPosition = "center center" }) => {
  const frame = useCurrentFrame();
  const t = frame / dur;

  const barHeight = interpolate(frame, [0, openSpeed], [42, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const scale = interpolate(t, [0, 1], [1.1, 1.0], { extrapolateRight: "clamp" });
  const tx = interpolate(t, [0, 1], [0, panX], { extrapolateRight: "clamp" });
  const imgBrightness = interpolate(frame, [0, 8, openSpeed * 0.7], [0.3, 0.6, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img
        src={staticFile(`photos/perch/${photo}`)}
        style={{
          position: "absolute", width: "100%", height: "100%",
          objectFit: "cover", objectPosition,
          transform: `scale(${scale}) translateX(${tx}px)`,
          transformOrigin: "center center",
          filter: `brightness(${imgBrightness})`,
        }}
      />
      {/* Top bar */}
      <div style={{
        position: "absolute", top: 0, width: "100%",
        height: `${barHeight}%`, backgroundColor: colors.ink,
      }} />
      {/* Bottom bar */}
      <div style={{
        position: "absolute", bottom: 0, width: "100%",
        height: `${barHeight}%`, backgroundColor: colors.ink,
      }} />
    </AbsoluteFill>
  );
};

// ── SPLIT FRAME — two photos stacked with gap ──
const SplitFrame: React.FC<{
  top: string;
  bottom: string;
  dur: number;
  topPosition?: string;
  bottomPosition?: string;
}> = ({ top, bottom, dur, topPosition = "center center", bottomPosition = "center center" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / dur;

  // Photos slide in from opposite sides
  const topSlide = spring({ frame, fps, config: { damping: 20, stiffness: 60 } });
  const bottomSlide = spring({ frame: frame - 3, fps, config: { damping: 20, stiffness: 60 } });

  const topX = interpolate(topSlide, [0, 1], [-40, 0]);
  const bottomX = interpolate(bottomSlide, [0, 1], [40, 0]);

  // Subtle zoom
  const zoom = interpolate(t, [0, 1], [1.02, 1.08], { extrapolateRight: "clamp" });

  const gap = 6;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      {/* Top half */}
      <div style={{
        position: "absolute", top: 0, left: 0, width: "100%",
        height: `calc(50% - ${gap / 2}px)`,
        overflow: "hidden",
        transform: `translateX(${topX}px)`,
      }}>
        <Img
          src={staticFile(`photos/perch/${top}`)}
          style={{
            width: "100%", height: "100%",
            objectFit: "cover", objectPosition: topPosition,
            transform: `scale(${zoom})`, transformOrigin: "center center",
          }}
        />
      </div>
      {/* Bottom half */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, width: "100%",
        height: `calc(50% - ${gap / 2}px)`,
        overflow: "hidden",
        transform: `translateX(${bottomX}px)`,
      }}>
        <Img
          src={staticFile(`photos/perch/${bottom}`)}
          style={{
            width: "100%", height: "100%",
            objectFit: "cover", objectPosition: bottomPosition,
            transform: `scale(${zoom})`, transformOrigin: "center center",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// ── BLUR TO SHARP — photo starts blurred and snaps into focus ──
const BlurReveal: React.FC<{
  photo: string;
  dur: number;
  panX?: number;
  objectPosition?: string;
}> = ({ photo, dur, panX = 6, objectPosition = "center center" }) => {
  const frame = useCurrentFrame();
  const t = frame / dur;

  const blur = interpolate(frame, [0, 12], [20, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const scale = interpolate(t, [0, 1], [1.06, 1.12], { extrapolateRight: "clamp" });
  const tx = interpolate(t, [0, 1], [0, panX], { extrapolateRight: "clamp" });
  const brightness = interpolate(frame, [0, 10], [0.7, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img
        src={staticFile(`photos/perch/${photo}`)}
        style={{
          position: "absolute", width: "100%", height: "100%",
          objectFit: "cover", objectPosition,
          transform: `scale(${scale}) translateX(${tx}px)`,
          transformOrigin: "center center",
          filter: `blur(${blur}px) brightness(${brightness})`,
        }}
      />
    </AbsoluteFill>
  );
};

// ── INSET FRAME — photo with border/margin, editorial feel ──
const InsetFrame: React.FC<{
  photo: string;
  dur: number;
  margin?: number;
  objectPosition?: string;
}> = ({ photo, dur, margin = 40, objectPosition = "center center" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / dur;

  const scaleIn = spring({ frame, fps, config: { damping: 22, stiffness: 55 } });
  const photoScale = interpolate(scaleIn, [0, 1], [0.92, 1]);
  const zoom = interpolate(t, [0, 1], [1.0, 1.06], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={{
        position: "absolute",
        top: margin, left: margin, right: margin, bottom: margin,
        overflow: "hidden",
        transform: `scale(${photoScale})`,
        transformOrigin: "center center",
      }}>
        <Img
          src={staticFile(`photos/perch/${photo}`)}
          style={{
            width: "100%", height: "100%",
            objectFit: "cover", objectPosition,
            transform: `scale(${zoom})`, transformOrigin: "center center",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// ── END CARD ──
const EndCard: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgZoom = interpolate(frame, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" });
  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const lineIn = spring({ frame: frame - 8, fps, config: { damping: 18, stiffness: 80 } });
  const nameIn = spring({ frame: frame - 14, fps, config: { damping: 16, stiffness: 70 } });
  const handleIn = spring({ frame: frame - 24, fps, config: { damping: 16, stiffness: 70 } });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img src={staticFile("photos/perch/twilight_hero.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover",
        transform: `scale(${bgZoom})`, transformOrigin: "center center",
        filter: "brightness(0.1) saturate(0.3)",
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
        opacity: fadeIn,
      }}>
        <div style={{
          width: lineIn * 60, height: 1,
          backgroundColor: colors.gold, marginBottom: 24, opacity: 0.5,
        }} />
        <div style={{
          fontFamily: fonts.sans, fontSize: 20, fontWeight: 400,
          color: colors.paper, letterSpacing: "0.1em",
          opacity: Math.min(nameIn * 2, 1),
          transform: `translateY(${(1 - nameIn) * 8}px)`,
        }}>
          Matt Anthony
        </div>
        <div style={{
          fontFamily: fonts.sans, fontSize: 15, fontWeight: 400,
          color: colors.stone, letterSpacing: "0.06em", marginTop: 6,
          opacity: Math.min(handleIn * 2, 1),
        }}>
          @mattanthonyphoto
        </div>
        <div style={{
          width: lineIn * 40, height: 1,
          backgroundColor: colors.gold, marginTop: 24, opacity: 0.3,
        }} />
      </div>
    </AbsoluteFill>
  );
};

// ── MAIN COMPOSITION ──
// Each segment uses a different layout to break visual pattern
// Hard cuts between segments — no crossfades
export const PerchDripHop: React.FC = () => {
  const B = Math.round(FPS * 0.55); // ~16 frames per beat unit

  // Timeline: mix of hold lengths for rhythm
  const seg = [
    B * 5,   // 1. letterbox reveal — aerial (long, sets the tone)
    B * 4,   // 2. full — entry exterior (hold)
    B * 2,   // 3. blur reveal — hallway (quick snap)
    B * 4,   // 4. split — kitchen + fireplace
    B * 3,   // 5. inset — cantilever (editorial)
    B * 2,   // 6. full — rear exterior (quick)
    B * 3,   // 7. blur reveal — side exterior
    B * 5,   // 8. full — twilight hero (linger)
  ];

  const endDur = TOTAL_FRAMES - seg.reduce((a, b) => a + b, 0);
  let f = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Audio
        src={staticFile("music2.mp3")}
        volume={(fr) => {
          const fadeIn = Math.min(fr / (1.5 * FPS), 1);
          const fadeOutStart = (TOTAL_SECONDS - 3) * FPS;
          const fadeOut = fr > fadeOutStart ? 1 - ((fr - fadeOutStart) / (3 * FPS)) : 1;
          return 0.65 * fadeIn * Math.max(0, fadeOut);
        }}
      />

      {/* 1. LETTERBOX REVEAL — aerial, bars open */}
      <Sequence from={f} durationInFrames={seg[0]}>
        <LetterboxReveal
          photo="aerial.jpg"
          dur={seg[0]}
          openSpeed={40}
          panX={-6}
        />
      </Sequence>
      {(() => { f += seg[0]; return null; })()}

      {/* 2. FULL — entry, hard cut, slow drift */}
      <Sequence from={f} durationInFrames={seg[1]}>
        <FullPhoto
          photo="entry.jpg"
          dur={seg[1]}
          startScale={1.05}
          endScale={1.12}
          panX={-8}
        />
      </Sequence>
      {(() => { f += seg[1]; return null; })()}

      {/* 3. BLUR REVEAL — hallway snaps into focus */}
      <Sequence from={f} durationInFrames={seg[2]}>
        <BlurReveal
          photo="hallway.jpg"
          dur={seg[2]}
          panX={0}
          objectPosition="center 25%"
        />
      </Sequence>
      {(() => { f += seg[2]; return null; })()}

      {/* 4. SPLIT FRAME — kitchen top, fireplace bottom */}
      <Sequence from={f} durationInFrames={seg[3]}>
        <SplitFrame
          top="kitchen.jpg"
          bottom="fireplace.jpg"
          dur={seg[3]}
          topPosition="center 40%"
          bottomPosition="center 35%"
        />
      </Sequence>
      {(() => { f += seg[3]; return null; })()}

      {/* 5. INSET — cantilever, editorial border */}
      <Sequence from={f} durationInFrames={seg[4]}>
        <InsetFrame
          photo="cantilever.jpg"
          dur={seg[4]}
          margin={36}
        />
      </Sequence>
      {(() => { f += seg[4]; return null; })()}

      {/* 6. FULL — rear exterior, quick cut */}
      <Sequence from={f} durationInFrames={seg[5]}>
        <FullPhoto
          photo="rear.jpg"
          dur={seg[5]}
          startScale={1.0}
          endScale={1.1}
          panX={6}
          panY={-3}
        />
      </Sequence>
      {(() => { f += seg[5]; return null; })()}

      {/* 7. BLUR REVEAL — side exterior */}
      <Sequence from={f} durationInFrames={seg[6]}>
        <BlurReveal
          photo="side.jpg"
          dur={seg[6]}
          panX={-5}
        />
      </Sequence>
      {(() => { f += seg[6]; return null; })()}

      {/* 8. FULL — twilight hero, the payoff */}
      <Sequence from={f} durationInFrames={seg[7]}>
        <FullPhoto
          photo="twilight_hero.jpg"
          dur={seg[7]}
          startScale={1.12}
          endScale={1.0}
          panX={-4}
        />
      </Sequence>
      {(() => { f += seg[7]; return null; })()}

      {/* END CARD */}
      <Sequence from={f} durationInFrames={endDur}>
        <EndCard dur={endDur} />
      </Sequence>

      {/* Global overlays */}
      <Sequence from={0} durationInFrames={TOTAL_FRAMES}><Grain /></Sequence>
    </AbsoluteFill>
  );
};
