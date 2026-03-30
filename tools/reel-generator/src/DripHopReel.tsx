import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, spring,
  useCurrentFrame, useVideoConfig, interpolate, staticFile,
} from "remotion";
import { colors, fonts } from "./brand";

const TOTAL_SECONDS = 32;
const FPS = 30;

// ── FILM GRAIN ──
const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{
      position: "absolute", inset: 0,
      opacity: 0.03, mixBlendMode: "overlay", pointerEvents: "none",
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' seed='${Math.floor(frame * 1.7)}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
      backgroundSize: "150px 150px",
    }} />
  );
};

// ── VIGNETTE ──
const Vig: React.FC = () => (
  <div style={{
    position: "absolute", inset: 0, pointerEvents: "none",
    background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.5) 100%)",
  }} />
);

// ── CROSSFADE PHOTO — Ken Burns pan/zoom with directional movement ──
interface DripSlide {
  photo: string;
  startScale: number;
  endScale: number;
  startX: number;
  endX: number;
  startY: number;
  endY: number;
  objectPosition?: string;
}

const DripPhoto: React.FC<{ slide: DripSlide; dur: number; fadeIn?: number; fadeOut?: number }> = ({
  slide, dur, fadeIn = 8, fadeOut = 8,
}) => {
  const frame = useCurrentFrame();
  const progress = frame / dur;

  const scale = interpolate(progress, [0, 1], [slide.startScale, slide.endScale], {
    extrapolateRight: "clamp",
  });
  const tx = interpolate(progress, [0, 1], [slide.startX, slide.endX], {
    extrapolateRight: "clamp",
  });
  const ty = interpolate(progress, [0, 1], [slide.startY, slide.endY], {
    extrapolateRight: "clamp",
  });

  // Opacity envelope for smooth crossfade
  const opacity = interpolate(frame, [0, fadeIn, dur - fadeOut, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        src={staticFile(`photos/${slide.photo}`)}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: slide.objectPosition || "center center",
          transform: `scale(${scale}) translate(${tx}px, ${ty}px)`,
          transformOrigin: "center center",
        }}
      />
    </AbsoluteFill>
  );
};

// ── PROJECT LABEL — fades in over the photo ──
const ProjectLabel: React.FC<{
  name: string;
  location: string;
  delay?: number;
}> = ({ name, location, delay = 6 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const labelIn = spring({ frame: frame - delay, fps, config: { damping: 16, stiffness: 80 } });

  return (
    <div style={{
      position: "absolute", bottom: 180, width: "100%", textAlign: "center",
      opacity: Math.min(labelIn * 2.5, 1),
      transform: `translateY(${(1 - labelIn) * 15}px)`,
    }}>
      <div style={{
        fontFamily: fonts.display, fontSize: 32, fontWeight: 700,
        color: colors.gold, letterSpacing: "0.14em",
        textShadow: "0 2px 20px rgba(0,0,0,0.9)",
      }}>
        {name}
      </div>
      <div style={{
        fontFamily: fonts.sans, fontSize: 20, fontWeight: 400,
        color: colors.lightStone, marginTop: 6, letterSpacing: "0.06em",
        textShadow: "0 1px 12px rgba(0,0,0,0.8)",
      }}>
        {location}
      </div>
    </div>
  );
};

// ── HOOK TEXT — cinematic count-in ──
const HookText: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const line1In = spring({ frame: frame - 4, fps, config: { damping: 14, stiffness: 90 } });
  const line2In = spring({ frame: frame - 14, fps, config: { damping: 14, stiffness: 80 } });

  // Subtle scale pulse
  const scale1 = interpolate(line1In, [0, 0.5, 0.8, 1], [0.6, 1.05, 0.98, 1]);
  const scale2 = interpolate(line2In, [0, 0.5, 0.8, 1], [0.6, 1.04, 0.98, 1]);

  // Fade out at end
  const fadeOut = interpolate(frame, [dur - 10, dur], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{
      backgroundColor: colors.ink, opacity: fadeOut,
      display: "flex", flexDirection: "column",
      justifyContent: "center", alignItems: "center",
    }}>
      {/* Subtle radial glow */}
      <div style={{
        position: "absolute", inset: 0,
        background: `radial-gradient(ellipse at center, rgba(201,169,110,0.04) 0%, transparent 60%)`,
      }} />

      <div style={{
        fontFamily: fonts.sans, fontSize: 40, fontWeight: 400,
        color: colors.stone, letterSpacing: "0.03em",
        opacity: Math.min(line1In * 3, 1),
        transform: `scale(${scale1})`,
        textShadow: "0 2px 20px rgba(0,0,0,0.5)",
      }}>
        5 homes.
      </div>
      <div style={{
        fontFamily: fonts.serif, fontSize: 56, fontWeight: 300,
        color: colors.paper, marginTop: 12,
        opacity: Math.min(line2In * 3, 1),
        transform: `scale(${scale2})`,
        textShadow: "0 2px 25px rgba(0,0,0,0.5)",
        fontStyle: "italic", letterSpacing: "0.02em",
      }}>
        1 photographer.
      </div>

      {/* Thin gold line accent */}
      <div style={{
        width: interpolate(line2In, [0, 1], [0, 100]),
        height: 1.5,
        backgroundColor: colors.gold,
        marginTop: 24,
        opacity: 0.7,
      }} />
    </AbsoluteFill>
  );
};

// ── END CTA ──
const EndCard: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgZoom = interpolate(frame, [0, dur], [1.0, 1.12], { extrapolateRight: "clamp" });
  const lineIn = spring({ frame: frame - 3, fps, config: { damping: 15, stiffness: 100 } });
  const titleIn = spring({ frame: frame - 8, fps, config: { damping: 12, stiffness: 75 } });
  const handleIn = spring({ frame: frame - 18, fps, config: { damping: 14, stiffness: 80 } });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img src={staticFile("photos/perch/twilight_hero.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover",
        transform: `scale(${bgZoom})`, transformOrigin: "center center",
        filter: "brightness(0.15) saturate(0.5)",
      }} />
      <div style={{
        position: "absolute", inset: 0,
        background: "linear-gradient(rgba(26,26,24,0.3) 0%, rgba(26,26,24,0.8) 50%, rgba(26,26,24,0.95) 100%)",
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
      }}>
        <div style={{
          width: lineIn * 160, height: 1.5,
          backgroundColor: colors.gold, marginBottom: 28, opacity: 0.8,
        }} />

        <div style={{
          fontFamily: fonts.serif, fontSize: 48, fontWeight: 300,
          color: colors.paper, textAlign: "center", lineHeight: 1.3,
          opacity: Math.min(titleIn * 2, 1),
          transform: `translateY(${(1 - titleIn) * 15}px)`,
          textShadow: "0 2px 25px rgba(0,0,0,0.6)",
          padding: "0 60px",
        }}>
          Your project,
        </div>
        <div style={{
          fontFamily: fonts.serif, fontSize: 52, fontWeight: 300,
          color: colors.gold, textAlign: "center", marginTop: 6,
          opacity: Math.min(titleIn * 2, 1),
          transform: `translateY(${(1 - titleIn) * 12}px)`,
          textShadow: "0 2px 25px rgba(0,0,0,0.6)",
          fontStyle: "italic",
        }}>
          seen differently.
        </div>

        <div style={{
          width: lineIn * 100, height: 1.5,
          backgroundColor: colors.gold, marginTop: 30, opacity: 0.5,
        }} />

        <div style={{
          fontFamily: fonts.sans, fontSize: 24, color: colors.paper,
          marginTop: 22, opacity: Math.min(handleIn * 2, 1),
          letterSpacing: "0.03em",
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>
          mattanthonyphoto.com
        </div>
        <div style={{
          fontFamily: fonts.sans, fontSize: 22, fontWeight: 500,
          color: colors.stone, marginTop: 10,
          opacity: Math.min(handleIn * 2, 1),
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>
          @mattanthonyphoto
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── SLIDE DATA ──
// Each slide: slow directional pan + subtle zoom, crossfading into the next
// Alternating directions to create the "drip" flow effect
const slides: (DripSlide & { label?: string; location?: string })[] = [
  // 1. Fitzsimmons twilight — slow zoom out, drift right
  {
    photo: "fitz_b.jpg",
    startScale: 1.2, endScale: 1.05,
    startX: -15, endX: 10,
    startY: 0, endY: -5,
    label: "FITZSIMMONS RESIDENCE", location: "WHISTLER, BC",
  },
  // 2. Warbler exterior — zoom in, drift left
  {
    photo: "warbler_a.jpg",
    startScale: 1.05, endScale: 1.18,
    startX: 12, endX: -8,
    startY: 5, endY: -3,
    label: "WARBLER RESIDENCE", location: "WHISTLER, BC",
  },
  // 3. Sugarloaf — zoom out, drift up
  {
    photo: "sugar_a.jpg",
    startScale: 1.15, endScale: 1.02,
    startX: -8, endX: 5,
    startY: 10, endY: -5,
    label: "SUGARLOAF RESIDENCE", location: "PEMBERTON, BC",
  },
  // 4. Eagle aerial — zoom in slowly, drift right
  {
    photo: "eagle_a.jpg",
    startScale: 1.0, endScale: 1.15,
    startX: -10, endX: 8,
    startY: -3, endY: 3,
    label: "EAGLE RESIDENCE", location: "PEMBERTON, BC",
  },
  // 5. Perch twilight hero — zoom out for the big reveal
  {
    photo: "perch/twilight_hero.jpg",
    startScale: 1.2, endScale: 1.0,
    startX: 8, endX: -5,
    startY: 5, endY: 0,
    label: "THE PERCH", location: "SQUAMISH, BC",
  },
  // 6. Fitz interior — intimate zoom in
  {
    photo: "fitz_int.jpg",
    startScale: 1.05, endScale: 1.18,
    startX: -5, endX: 8,
    startY: 0, endY: -5,
    objectPosition: "center 40%",
  },
  // 7. Perch kitchen — slow drift
  {
    photo: "perch/kitchen.jpg",
    startScale: 1.08, endScale: 1.0,
    startX: 10, endX: -5,
    startY: -5, endY: 3,
    objectPosition: "center 35%",
  },
  // 8. Warbler detail — zoom out
  {
    photo: "warbler_c.jpg",
    startScale: 1.2, endScale: 1.05,
    startX: -8, endX: 6,
    startY: 3, endY: -3,
  },
  // 9. Perch cantilever — zoom in, the final shot before CTA
  {
    photo: "perch/cantilever.jpg",
    startScale: 1.0, endScale: 1.15,
    startX: 5, endX: -8,
    startY: -5, endY: 5,
  },
];

// ── MAIN COMPOSITION ──
export const DripHopReel: React.FC = () => {
  const HOOK_DUR = 3 * FPS; // 3 seconds
  const END_DUR = 5 * FPS;  // 5 seconds
  const SLIDE_BODY = TOTAL_SECONDS * FPS - HOOK_DUR - END_DUR;
  const OVERLAP = 8; // crossfade overlap in frames
  const SLIDE_DUR = Math.floor((SLIDE_BODY + OVERLAP * (slides.length - 1)) / slides.length);

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Audio
        src={staticFile("music2.mp3")}
        volume={(fr) => {
          const fadeIn = Math.min(fr / (1.5 * FPS), 1);
          const fadeOutStart = (TOTAL_SECONDS - 3) * FPS;
          const fadeOut = fr > fadeOutStart ? 1 - ((fr - fadeOutStart) / (3 * FPS)) : 1;
          return 0.7 * fadeIn * Math.max(0, fadeOut);
        }}
      />

      {/* HOOK */}
      <Sequence from={0} durationInFrames={HOOK_DUR}>
        <HookText dur={HOOK_DUR} />
      </Sequence>

      {/* DRIP HOP SLIDES — overlapping crossfades */}
      {slides.map((slide, i) => {
        const startFrame = HOOK_DUR + i * (SLIDE_DUR - OVERLAP);
        const isFirst = i === 0;
        const isLast = i === slides.length - 1;

        return (
          <Sequence key={i} from={startFrame} durationInFrames={SLIDE_DUR}>
            <DripPhoto
              slide={slide}
              dur={SLIDE_DUR}
              fadeIn={isFirst ? 6 : OVERLAP}
              fadeOut={isLast ? 6 : OVERLAP}
            />
            {/* Bottom gradient for label readability */}
            {slide.label && (
              <div style={{
                position: "absolute", bottom: 0, width: "100%", height: "45%",
                background: "linear-gradient(transparent, rgba(0,0,0,0.7))",
                pointerEvents: "none",
              }} />
            )}
            {slide.label && slide.location && (
              <ProjectLabel name={slide.label} location={slide.location} delay={10} />
            )}
          </Sequence>
        );
      })}

      {/* END CTA */}
      <Sequence from={TOTAL_SECONDS * FPS - END_DUR} durationInFrames={END_DUR}>
        <EndCard dur={END_DUR} />
      </Sequence>

      {/* Global overlays */}
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * FPS}>
        <Grain />
      </Sequence>
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * FPS}>
        <Vig />
      </Sequence>
    </AbsoluteFill>
  );
};
