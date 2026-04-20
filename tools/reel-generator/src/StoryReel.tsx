import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, spring,
  useCurrentFrame, useVideoConfig, interpolate, staticFile, continueRender, delayRender,
} from "remotion";
import { lrdColors, lrdFonts } from "./lrd-brand";

// =============================================================
// LRD Story Pipeline — 9:16 animated-text frames for IG Stories.
// Generic StoryFrame + StoryReel driven by a per-sequence config.
// =============================================================

// --- Register the Cormorant Garamond local font so renders use it,
// --- not the Georgia fallback. @font-face is applied once on module load.
if (typeof document !== "undefined") {
  const id = "lrd-font-face";
  if (!document.getElementById(id)) {
    const style = document.createElement("style");
    style.id = id;
    style.innerHTML = `
      @font-face {
        font-family: 'Cormorant Garamond';
        src: url(${staticFile("fonts/CormorantGaramond-Light.ttf")}) format('truetype');
        font-weight: 300;
        font-style: normal;
        font-display: block;
      }
      @font-face {
        font-family: 'Cormorant Garamond';
        src: url(${staticFile("fonts/CormorantGaramond-Regular.ttf")}) format('truetype');
        font-weight: 400;
        font-style: normal;
        font-display: block;
      }
      @font-face {
        font-family: 'Cormorant Garamond';
        src: url(${staticFile("fonts/CormorantGaramond-Bold.ttf")}) format('truetype');
        font-weight: 700;
        font-style: normal;
        font-display: block;
      }
      @font-face {
        font-family: 'DM Sans';
        src: url(${staticFile("fonts/DMSans-Regular.ttf")}) format('truetype');
        font-weight: 400;
        font-style: normal;
        font-display: block;
      }
      @font-face {
        font-family: 'Josefin Sans';
        src: url(${staticFile("fonts/JosefinSans-Regular.ttf")}) format('truetype');
        font-weight: 400;
        font-style: normal;
        font-display: block;
      }
      @font-face {
        font-family: 'Josefin Sans';
        src: url(${staticFile("fonts/JosefinSans-Bold.ttf")}) format('truetype');
        font-weight: 700;
        font-style: normal;
        font-display: block;
      }
    `;
    document.head.appendChild(style);
    // Nudge the browser to block rendering until fonts actually load.
    const handle = delayRender("loading-lrd-fonts");
    (document as any).fonts?.ready.then(() => continueRender(handle)).catch(() => continueRender(handle));
  }
}

// ----------------------------------------------
// Config types
// ----------------------------------------------
export interface StoryFrameConfig {
  photo: string;           // path relative to public/ (e.g. "lrd-sunstone/7150.jpg")
  text: string;
  duration?: number;       // seconds, default 4
}

export interface StoryConfig {
  id: string;              // composition id (no underscores)
  title: string;
  frames: StoryFrameConfig[];
  musicFile?: string;      // optional filename relative to public/music-library/
}

// ----------------------------------------------
// StoryFrame — a single 9:16 frame for one duration
// ----------------------------------------------
interface StoryFrameProps {
  photo: string;
  text: string;
  durationFrames: number;
}

export const StoryFrame: React.FC<StoryFrameProps> = ({ photo, text, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Ken Burns: 1.0 -> 1.06 over duration
  const zoom = interpolate(frame, [0, durationFrames], [1.0, 1.06], { extrapolateRight: "clamp" });

  // Text animate IN: opacity 0->1, translateY 40->0, spring (damping 18, mass 0.8)
  const inSpring = spring({
    frame,
    fps,
    config: { damping: 18, mass: 0.8, stiffness: 100 },
    durationInFrames: 25,
  });

  // Text animate OUT over last 15 frames: opacity 1->0, translateY 0 -> -20
  const outStart = durationFrames - 15;
  const outProgress = interpolate(frame, [outStart, durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const opacity = Math.min(inSpring, 1 - outProgress);
  const translateY = (1 - inSpring) * 40 + outProgress * -20;

  return (
    <AbsoluteFill style={{ backgroundColor: lrdColors.ink, overflow: "hidden" }}>
      {/* Photo — fills frame with subtle Ken Burns zoom */}
      <Img
        src={staticFile(photo)}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: "center center",
          transform: `scale(${zoom})`,
          transformOrigin: "center center",
        }}
      />

      {/* Darkening gradient from bottom 40% for text legibility */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          height: "55%",
          background:
            "linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.25) 45%, rgba(0,0,0,0.72) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Text block: centered horizontally, sits in bottom third (y ~1200) */}
      <div
        style={{
          position: "absolute",
          top: 1200,
          left: 0,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "flex-start",
          opacity,
          transform: `translateY(${translateY}px)`,
        }}
      >
        {/* Gold/taupe accent line — 1px, 60px wide, 24px above text */}
        <div
          style={{
            width: 60,
            height: 1,
            backgroundColor: "#C9A96E",
            marginBottom: 24,
            opacity,
          }}
        />
        <div
          style={{
            fontFamily: lrdFonts.geometric,
            fontSize: 54,
            fontWeight: 400,
            color: "#FFFFFF",
            lineHeight: 1.25,
            letterSpacing: "1.5px",
            maxWidth: 820,
            textAlign: "center",
            textShadow: "0 2px 20px rgba(0,0,0,0.4)",
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ----------------------------------------------
// Flash transition — 8-frame white flash peaking at midpoint
// ----------------------------------------------
const FlashTransition: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, dur / 2, dur], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{ backgroundColor: `rgba(255,255,255,${o})`, pointerEvents: "none", zIndex: 100 }}
    />
  );
};

// ----------------------------------------------
// StoryReel — composes multiple StoryFrames back-to-back
// ----------------------------------------------
const FLASH_FRAMES = 8;
const MUSIC_FADE_FRAMES = 30;
const MUSIC_PEAK_VOLUME = 0.75;

export const StoryReel: React.FC<{ config: StoryConfig }> = ({ config }) => {
  const { fps } = useVideoConfig();
  const fragments: React.ReactNode[] = [];

  let f = 0;
  config.frames.forEach((fc, i) => {
    const durSec = fc.duration ?? 4;
    const durFrames = Math.round(durSec * fps);

    fragments.push(
      <Sequence key={`f${i}`} from={f} durationInFrames={durFrames}>
        <StoryFrame photo={fc.photo} text={fc.text} durationFrames={durFrames} />
      </Sequence>
    );

    // Flash at the boundary — straddle the seam so it's visible across both frames.
    if (i < config.frames.length - 1) {
      const flashStart = f + durFrames - Math.floor(FLASH_FRAMES / 2);
      fragments.push(
        <Sequence key={`flash${i}`} from={flashStart} durationInFrames={FLASH_FRAMES}>
          <FlashTransition dur={FLASH_FRAMES} />
        </Sequence>
      );
    }

    f += durFrames;
  });

  // Total duration in frames, used for audio fade-out math.
  const totalFrames = f;

  return (
    <AbsoluteFill style={{ backgroundColor: lrdColors.ink }}>
      {config.musicFile ? (
        <Audio
          src={staticFile("music-library/" + config.musicFile)}
          volume={(frame) => {
            // Fade in: 0 -> peak over first MUSIC_FADE_FRAMES frames
            // Fade out: peak -> 0 over final MUSIC_FADE_FRAMES frames
            const fadeIn = interpolate(
              frame,
              [0, MUSIC_FADE_FRAMES],
              [0, MUSIC_PEAK_VOLUME],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            const fadeOut = interpolate(
              frame,
              [totalFrames - MUSIC_FADE_FRAMES, totalFrames],
              [MUSIC_PEAK_VOLUME, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            return Math.min(fadeIn, fadeOut);
          }}
        />
      ) : null}
      {fragments}
    </AbsoluteFill>
  );
};

// Helper: compute total seconds for a config (so Root can size the composition).
export const totalSecondsForStory = (config: StoryConfig): number => {
  return config.frames.reduce((sum, fr) => sum + (fr.duration ?? 4), 0);
};
