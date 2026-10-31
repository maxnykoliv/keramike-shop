/** Tile swatch colors used until there is a photo. This is content, not UI colors. */
const PALETTE: Array<[RegExp, string, string]> = [
  [/сір|grey|gray/i, "#c9c6c0", "#b9b5ae"],
  [/біл|white/i, "#efece6", "#e2ddd4"],
  [/беж|sand|пісоч/i, "#d8c8b0", "#cbb89c"],
  [/м.ятн|mint|зелен/i, "#b9cfc3", "#a9c1b4"],
  [/чорн|графіт|black/i, "#4a4844", "#3d3b38"],
  [/корич|дерев|oak|wood/i, "#a88a69", "#977a5b"],
  [/син|blue/i, "#9fb0bf", "#8fa1b1"],
];
const DEFAULT: [string, string] = ["#ddd5c8", "#d0c6b6"];

export function swatchColors(color: string | null | undefined): [string, string] {
  for (const [pattern, base, joint] of PALETTE) if (color && pattern.test(color)) return [base, joint];
  return DEFAULT;
}
