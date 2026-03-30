import React from "react";
import {
  AbsoluteFill, Img, staticFile,
} from "remotion";
import { colors, fonts } from "./brand";

const GAP = 5;

// ── MAIN COMPOSITION — 1080x1350 pinned post ──
export const BookingPost: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>

      {/* ── TOP ROW: one wide landscape ── */}
      <div style={{
        position: "absolute",
        top: 0, left: 0, right: 0,
        height: 420,
        overflow: "hidden",
      }}>
        <Img
          src={staticFile("photos/perch/twilight_hero.jpg")}
          style={{
            width: "100%", height: "100%",
            objectFit: "cover", objectPosition: "center 55%",
          }}
        />
      </div>

      {/* ── MIDDLE ROW: three squares ── */}
      <div style={{
        position: "absolute",
        top: 420 + GAP, left: 0, right: 0,
        height: 355,
        display: "flex", gap: GAP,
      }}>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <Img
            src={staticFile("photos/perch/hallway.jpg")}
            style={{
              width: "100%", height: "100%",
              objectFit: "cover", objectPosition: "center 20%",
            }}
          />
        </div>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <Img
            src={staticFile("photos/perch/fireplace.jpg")}
            style={{
              width: "100%", height: "100%",
              objectFit: "cover", objectPosition: "center 35%",
            }}
          />
        </div>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <Img
            src={staticFile("photos/perch/cantilever.jpg")}
            style={{
              width: "100%", height: "100%",
              objectFit: "cover", objectPosition: "center center",
            }}
          />
        </div>
      </div>

      {/* ── BOTTOM ROW: two panels — landscape + square ── */}
      <div style={{
        position: "absolute",
        top: 420 + GAP + 355 + GAP, left: 0, right: 0,
        height: 340,
        display: "flex", gap: GAP,
      }}>
        <div style={{ flex: 1.6, overflow: "hidden" }}>
          <Img
            src={staticFile("photos/perch/kitchen.jpg")}
            style={{
              width: "100%", height: "100%",
              objectFit: "cover", objectPosition: "center 40%",
            }}
          />
        </div>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <Img
            src={staticFile("photos/perch/entry.jpg")}
            style={{
              width: "100%", height: "100%",
              objectFit: "cover", objectPosition: "center center",
            }}
          />
        </div>
      </div>

      {/* ── TEXT STRIP — bottom ── */}
      <div style={{
        position: "absolute",
        bottom: 0, left: 0, right: 0,
        height: 220,
        background: `linear-gradient(transparent 0%, rgba(26,26,24,0.85) 35%, ${colors.ink} 100%)`,
        display: "flex", flexDirection: "column",
        justifyContent: "flex-end", alignItems: "center",
        paddingBottom: 38,
      }}>
        <div style={{
          width: 50, height: 1,
          backgroundColor: colors.gold, opacity: 0.5,
          marginBottom: 18,
        }} />
        <div style={{
          fontFamily: fonts.sans, fontSize: 14, fontWeight: 400,
          color: colors.stone, letterSpacing: "0.25em",
          textTransform: "uppercase",
        }}>
          Now Booking
        </div>
        <div style={{
          fontFamily: fonts.serif, fontSize: 38, fontWeight: 300,
          color: colors.paper, letterSpacing: "0.02em",
          marginTop: 4, fontStyle: "italic",
        }}>
          Spring &amp; Summer 2026
        </div>
        <div style={{
          fontFamily: fonts.sans, fontSize: 13, fontWeight: 400,
          color: colors.stone, letterSpacing: "0.12em",
          marginTop: 14,
        }}>
          MATTANTHONYPHOTO.COM
        </div>
      </div>
    </AbsoluteFill>
  );
};
