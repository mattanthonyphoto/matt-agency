// LRD Studio brand tokens — refined, calm, feminine-masculine balance.
// NOT Matt's gold — LRD uses warm taupe + dark ink + off-white + serif display.
export const lrdColors = {
  ink: "#1C1A17",          // dark ink (nearly black, slightly warm)
  paper: "#F4EFE6",        // off-white background
  taupe: "#A48F72",        // warm taupe accent
  taupeLight: "#C8B79A",   // lighter taupe for subtle lines
  stone: "#8F8775",        // muted stone text
  offWhite: "#EFE9DE",     // slightly cooler off-white for text
} as const;

export const lrdFonts = {
  serif: "'Cormorant Garamond', Georgia, serif",
  sans: "'DM Sans', -apple-system, sans-serif",
  // Matches the font loaded on lrdstudio.ca — Poppins is LRD's actual brand font.
  brand: "'Poppins', -apple-system, 'Helvetica Neue', sans-serif",
} as const;
