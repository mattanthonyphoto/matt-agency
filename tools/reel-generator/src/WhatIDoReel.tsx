import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, spring,
  useCurrentFrame, useVideoConfig, interpolate, staticFile,
} from "remotion";
import { colors, fonts } from "./brand";

const TOTAL_SECONDS = 28;

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

// ===== WARM COLOR GRADE =====
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

// ===== TEXT PUNCH — big text that slams in =====
const TextPunch: React.FC<{
  line1: string;
  line2?: string;
  line1Color?: string;
  line2Color?: string;
  line1Size?: number;
  line2Size?: number;
}> = ({ line1, line2, line1Color = colors.paper, line2Color = colors.gold, line1Size = 52, line2Size = 72 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s1 = spring({ frame: frame - 2, fps, config: { damping: 10, stiffness: 120 } });
  const s2 = spring({ frame: frame - 6, fps, config: { damping: 10, stiffness: 100 } });

  // Slight bounce overshoot on scale
  const scale1 = interpolate(s1, [0, 0.5, 0.8, 1], [0.3, 1.08, 0.97, 1]);
  const scale2 = interpolate(s2, [0, 0.5, 0.8, 1], [0.3, 1.06, 0.98, 1]);

  return (
    <AbsoluteFill style={{
      display: "flex", flexDirection: "column",
      justifyContent: "center", alignItems: "center",
    }}>
      <div style={{
        fontFamily: fonts.sans, fontSize: line1Size, fontWeight: 500,
        color: line1Color, letterSpacing: "0.02em", textAlign: "center",
        opacity: Math.min(s1 * 3, 1), transform: `scale(${scale1})`,
        textShadow: "0 2px 20px rgba(0,0,0,0.8)",
        padding: "0 60px",
      }}>
        {line1}
      </div>
      {line2 && (
        <div style={{
          fontFamily: fonts.serif, fontSize: line2Size, fontWeight: 300,
          color: line2Color, textAlign: "center", marginTop: 10,
          opacity: Math.min(s2 * 3, 1), transform: `scale(${scale2})`,
          textShadow: "0 2px 25px rgba(0,0,0,0.8)",
          letterSpacing: "0.03em", fontStyle: "italic",
          padding: "0 50px",
        }}>
          {line2}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ===== PHOTO REVEAL — photo with overlay text label =====
const PhotoReveal: React.FC<{
  photo: string;
  label: string;
  sublabel?: string;
  dur: number;
  direction?: "left" | "right" | "up";
}> = ({ photo, label, sublabel, dur, direction = "left" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Photo zooms in slowly
  const zoom = interpolate(frame, [0, dur], [1.0, 1.12], { extrapolateRight: "clamp" });

  // Photo slides in from direction
  const si = spring({ frame, fps, config: { damping: 18, stiffness: 70 } });
  const slideX = direction === "left" ? (1 - si) * -80 : direction === "right" ? (1 - si) * 80 : 0;
  const slideY = direction === "up" ? (1 - si) * 60 : 0;

  // Label springs in
  const labelS = spring({ frame: frame - 5, fps, config: { damping: 12, stiffness: 90 } });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img src={staticFile(`photos/${photo}`)} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center 30%",
        transform: `scale(${zoom}) translate(${slideX}px, ${slideY}px)`,
        transformOrigin: "center center",
      }} />
      {/* Dark overlay for text readability */}
      <div style={{
        position: "absolute", bottom: 0, width: "100%", height: "55%",
        background: "linear-gradient(transparent, rgba(0,0,0,0.85))",
      }} />

      {/* Label */}
      <div style={{
        position: "absolute", bottom: 220, width: "100%", textAlign: "center",
        opacity: Math.min(labelS * 2.5, 1),
        transform: `translateY(${(1 - labelS) * 20}px)`,
      }}>
        <div style={{
          fontFamily: fonts.display, fontSize: 44, fontWeight: 700,
          color: colors.gold, letterSpacing: "0.12em",
          textShadow: "0 2px 20px rgba(0,0,0,0.8)",
        }}>
          {label}
        </div>
        {sublabel && (
          <div style={{
            fontFamily: fonts.sans, fontSize: 26, fontWeight: 400,
            color: colors.paper, marginTop: 8, letterSpacing: "0.03em",
            textShadow: "0 1px 15px rgba(0,0,0,0.7)",
          }}>
            {sublabel}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ===== RAPID FIRE — quick cuts of multiple photos =====
const RapidFire: React.FC<{ photos: string[]; dur: number }> = ({ photos, dur }) => {
  const frame = useCurrentFrame();
  const framesPerPhoto = Math.floor(dur / photos.length);
  const currentIndex = Math.min(Math.floor(frame / framesPerPhoto), photos.length - 1);
  const localFrame = frame - currentIndex * framesPerPhoto;

  // Each photo zooms slightly
  const zoom = interpolate(localFrame, [0, framesPerPhoto], [1.0, 1.08], { extrapolateRight: "clamp" });

  // Slam-in scale
  const slamScale = interpolate(localFrame, [0, 2, 4], [1.15, 0.98, 1.0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: colors.ink }}>
      <Img
        src={staticFile(`photos/${photos[currentIndex]}`)}
        style={{
          position: "absolute", width: "100%", height: "100%",
          objectFit: "cover", objectPosition: "center center",
          transform: `scale(${zoom * slamScale})`,
          transformOrigin: "center center",
        }}
      />
    </AbsoluteFill>
  );
};

// ===== STATS COUNTER =====
const StatsReveal: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = frame / dur;

  const stats = [
    { value: 19, suffix: "+", label: "PROJECTS" },
    { value: 28, label: "CLIENTS" },
    { value: 7, label: "REGIONS" },
  ];

  return (
    <AbsoluteFill style={{
      backgroundColor: colors.ink,
      display: "flex", flexDirection: "column",
      justifyContent: "center", alignItems: "center", gap: 50,
    }}>
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        background: `radial-gradient(ellipse at center, #222220 0%, ${colors.ink} 70%)`,
      }} />

      {stats.map((stat, i) => {
        const delay = i * 8;
        const s = spring({ frame: frame - delay, fps, config: { damping: 10, stiffness: 100 } });
        const count = Math.round(interpolate(frame, [delay, delay + 20], [0, stat.value], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        }));
        const scale = interpolate(s, [0, 0.5, 0.8, 1], [0.5, 1.1, 0.97, 1]);

        return (
          <div key={stat.label} style={{
            position: "relative", zIndex: 1, textAlign: "center",
            opacity: Math.min(s * 3, 1),
            transform: `scale(${scale})`,
          }}>
            <div style={{
              fontFamily: fonts.display, fontSize: 80, fontWeight: 700,
              color: colors.gold, letterSpacing: "0.05em",
            }}>
              {count}{stat.suffix || ""}
            </div>
            <div style={{
              fontFamily: fonts.display, fontSize: 28, fontWeight: 700,
              color: colors.paper, letterSpacing: "0.2em", marginTop: -5,
            }}>
              {stat.label}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// ===== END CTA =====
const EndCTA: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgZoom = interpolate(frame, [0, dur], [1.0, 1.15], { extrapolateRight: "clamp" });

  const lineIn = spring({ frame: frame - 3, fps, config: { damping: 15, stiffness: 100 } });
  const titleIn = spring({ frame: frame - 6, fps, config: { damping: 12, stiffness: 75 } });
  const subIn = spring({ frame: frame - 12, fps, config: { damping: 14, stiffness: 80 } });
  const handleIn = spring({ frame: frame - 20, fps, config: { damping: 14, stiffness: 80 } });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img src={staticFile("photos/fitz_b.jpg")} style={{
        position: "absolute", width: "100%", height: "100%",
        objectFit: "cover", objectPosition: "center center",
        transform: `scale(${bgZoom})`, transformOrigin: "center center",
        filter: "brightness(0.18) saturate(0.6)",
      }} />
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        background: "linear-gradient(rgba(26,26,24,0.2) 0%, rgba(26,26,24,0.7) 50%, rgba(26,26,24,0.95) 100%)",
      }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center",
      }}>
        <div style={{ width: lineIn * 180, height: 2, backgroundColor: colors.gold, marginBottom: 30 }} />

        <div style={{
          fontFamily: fonts.serif, fontSize: 54, fontWeight: 300,
          color: colors.paper, textAlign: "center", lineHeight: 1.35,
          opacity: Math.min(titleIn * 2, 1),
          transform: `translateY(${(1 - titleIn) * 18}px)`,
          textShadow: "0 2px 25px rgba(0,0,0,0.6)",
          padding: "0 50px",
        }}>
          Not just a photographer.
        </div>

        <div style={{
          fontFamily: fonts.serif, fontSize: 58, fontWeight: 300,
          color: colors.gold, textAlign: "center", marginTop: 8,
          opacity: Math.min(subIn * 2, 1),
          transform: `translateY(${(1 - subIn) * 12}px)`,
          textShadow: "0 2px 25px rgba(0,0,0,0.6)",
          fontStyle: "italic",
        }}>
          A creative partner.
        </div>

        <div style={{ width: lineIn * 120, height: 2, backgroundColor: colors.gold, marginTop: 35, opacity: 0.6 }} />

        <div style={{
          fontFamily: fonts.sans, fontSize: 26, color: colors.paper,
          marginTop: 25, opacity: Math.min(handleIn * 2, 1),
          letterSpacing: "0.03em",
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>
          mattanthonyphoto.com
        </div>

        <div style={{
          fontFamily: fonts.sans, fontSize: 24, fontWeight: 500,
          color: colors.stone, marginTop: 12, opacity: Math.min(handleIn * 2, 1),
          textShadow: "0 1px 10px rgba(0,0,0,0.5)",
        }}>
          @mattanthonyphoto
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ===== MAIN COMPOSITION =====
export const WhatIDoReel: React.FC = () => {
  const { fps } = useVideoConfig();
  const BEAT = Math.round(0.625 * fps); // 19 frames at 30fps
  const FLASH = 3;

  // Timeline segments (in beats):
  // Hook text 1: "People think..." (2.5 beats)
  // Hook text 2: "...I just take photos of houses" (2.5 beats)
  // Rapid fire montage (3 beats) — fast cuts showing the work
  // Photo 1: EXTERIORS (2 beats)
  // Photo 2: INTERIORS (2 beats)
  // Photo 3: TWILIGHT (2 beats)
  // Photo 4: AERIALS (2 beats)
  // Text punch: "But also..." (2 beats)
  // Rapid fire 2: websites, strategy, social (3 beats)
  // Stats reveal (3 beats)
  // End CTA (5 beats)

  const HOOK1 = BEAT * 4;
  const HOOK2 = BEAT * 4;
  const RAPID1 = BEAT * 4;
  const PHOTO_DUR = BEAT * 3;
  const TEXT_BRIDGE = BEAT * 3;
  const RAPID2 = BEAT * 3;
  const STATS = BEAT * 4;
  const END_DUR = (TOTAL_SECONDS * fps) - HOOK1 - HOOK2 - RAPID1 - (PHOTO_DUR * 4) - TEXT_BRIDGE - RAPID2 - STATS;

  let f = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Audio
        src={staticFile("music2.mp3")}
        volume={(fr) => {
          const fadeIn = Math.min(fr / (0.5 * 30), 1);
          const fadeOutStart = (TOTAL_SECONDS - 2.5) * 30;
          const fadeOut = fr > fadeOutStart ? 1 - ((fr - fadeOutStart) / (2.5 * 30)) : 1;
          return 0.8 * fadeIn * Math.max(0, fadeOut);
        }}
      />

      {/* HOOK 1: "People think..." */}
      <Sequence from={f} durationInFrames={HOOK1}>
        <AbsoluteFill style={{ backgroundColor: colors.ink }}>
          <TextPunch
            line1="People think..."
            line1Size={48}
            line1Color={colors.stone}
          />
        </AbsoluteFill>
      </Sequence>
      {(() => { f += HOOK1; return null; })()}

      {/* HOOK 2: "I just take photos of houses" */}
      <Sequence from={f} durationInFrames={HOOK2}>
        <AbsoluteFill style={{ backgroundColor: colors.ink }}>
          <TextPunch
            line1="I just take photos"
            line2="of houses."
            line1Size={44}
            line1Color={colors.paper}
            line2Color={colors.stone}
            line2Size={60}
          />
        </AbsoluteFill>
      </Sequence>
      <Sequence from={f + HOOK2 - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += HOOK2; return null; })()}

      {/* RAPID FIRE 1: Quick montage of best shots */}
      <Sequence from={f} durationInFrames={RAPID1}>
        <RapidFire
          photos={["warbler_a.jpg", "fitz_b.jpg", "sugar_a.jpg", "eagle_a.jpg", "warbler_b.jpg", "fitz_c.jpg"]}
          dur={RAPID1}
        />
      </Sequence>
      <Sequence from={f + RAPID1 - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += RAPID1; return null; })()}

      {/* PHOTO 1: EXTERIORS */}
      <Sequence from={f} durationInFrames={PHOTO_DUR}>
        <PhotoReveal
          photo="warbler_a.jpg"
          label="EXTERIORS"
          sublabel="Every angle. Every detail."
          dur={PHOTO_DUR}
          direction="left"
        />
      </Sequence>
      <Sequence from={f + PHOTO_DUR - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += PHOTO_DUR; return null; })()}

      {/* PHOTO 2: INTERIORS */}
      <Sequence from={f} durationInFrames={PHOTO_DUR}>
        <PhotoReveal
          photo="fitz_int.jpg"
          label="INTERIORS"
          sublabel="Light, texture, craftsmanship."
          dur={PHOTO_DUR}
          direction="right"
        />
      </Sequence>
      <Sequence from={f + PHOTO_DUR - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += PHOTO_DUR; return null; })()}

      {/* PHOTO 3: TWILIGHT */}
      <Sequence from={f} durationInFrames={PHOTO_DUR}>
        <PhotoReveal
          photo="fitz_b.jpg"
          label="TWILIGHT"
          sublabel="When architecture comes alive."
          dur={PHOTO_DUR}
          direction="up"
        />
      </Sequence>
      <Sequence from={f + PHOTO_DUR - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += PHOTO_DUR; return null; })()}

      {/* PHOTO 4: AERIALS */}
      <Sequence from={f} durationInFrames={PHOTO_DUR}>
        <PhotoReveal
          photo="eagle_a.jpg"
          label="AERIALS"
          sublabel="Context you can't get from the ground."
          dur={PHOTO_DUR}
          direction="left"
        />
      </Sequence>
      <Sequence from={f + PHOTO_DUR - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += PHOTO_DUR; return null; })()}

      {/* TEXT BRIDGE: "But wait there's more" moment */}
      <Sequence from={f} durationInFrames={TEXT_BRIDGE}>
        <AbsoluteFill style={{ backgroundColor: colors.ink }}>
          <TextPunch
            line1="Oh, and also..."
            line2="websites, SEO, strategy, video."
            line1Size={42}
            line1Color={colors.gold}
            line2Size={36}
            line2Color={colors.lightStone}
          />
        </AbsoluteFill>
      </Sequence>
      <Sequence from={f + TEXT_BRIDGE - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += TEXT_BRIDGE; return null; })()}

      {/* RAPID FIRE 2: More work, faster */}
      <Sequence from={f} durationInFrames={RAPID2}>
        <RapidFire
          photos={["sugar_b.jpg", "warbler_c.jpg", "fitz_a.jpg", "sugar_int.jpg"]}
          dur={RAPID2}
        />
      </Sequence>
      <Sequence from={f + RAPID2 - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += RAPID2; return null; })()}

      {/* STATS */}
      <Sequence from={f} durationInFrames={STATS}>
        <StatsReveal dur={STATS} />
      </Sequence>
      <Sequence from={f + STATS - FLASH} durationInFrames={FLASH + 2}><Flash dur={FLASH + 2} /></Sequence>
      {(() => { f += STATS; return null; })()}

      {/* END CTA */}
      <Sequence from={f} durationInFrames={END_DUR}>
        <EndCTA dur={END_DUR} />
      </Sequence>

      {/* Global overlays */}
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><FilmGrain /></Sequence>
      <Sequence from={0} durationInFrames={TOTAL_SECONDS * fps}><ColorGrade /></Sequence>
    </AbsoluteFill>
  );
};
