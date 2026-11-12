# Vast Compressed

A content mod for [Horizon](https://playhorizon.dev) (Minecraft 26.3 rewritten in Rust): the game's blocks packed
nine at a time, from **I** (9 blocks) to **IX** (387,420,489 blocks), and back.

- **92 blocks × 9 tiers = 828 compressed blocks.** Stone and its kinds, deepslate, tuff, calcite, netherrack,
  blackstone, basalt, end stone, obsidian, terracotta and all 16 concretes; dirt, sand, gravel, clay, mud, soul sand
  and snow; every log and plank; moss, hay, kelp, wart blocks and sponge; pumpkin and melon; coal, iron, gold,
  copper, raw ores, redstone, lapis, diamond, emerald and netherite; glass, glowstone, magma and blue ice.
- **Crafting:** nine of a block (or of a tier) in the 3 × 3 grid make the next tier; one block of a tier gives
  nine of the tier below.
- **Each tier is marked** by a frame drawn over the block: steel for I–III, brass for IV–VI, violet for VII–IX,
  with corner plates on the second tier of each band and rivets on the third. The tooltip says how many blocks it
  holds.
- Each tier is a quarter harder to mine and to blow up than the one below. Glowstone and magma still glow, blue
  ice is still slippery; sand and gravel don't fall, dirt can't be tilled.
- Names in **English and Brazilian Portuguese** ("Compressed Cobblestone III", "Pedregulho Compactado III").
- Tags: `vastcompressed:compressed` (every block) and `vastcompressed:compressed/<block>` (one block's nine tiers).

## Install

Put `vastcompressed-<version>.hmod` in Horizon's mods (or install it from the launcher) and restart. Data only:
nothing to build.

## Building

`python3 tools/build_content.py build` writes the mod into `build/vastcompressed`; `./release.sh` packs
`dist/vastcompressed-<version>.hmod`; `./apply.sh` installs it locally. `tools/icon.py` draws the icon.

## Art and credits

The nine overlays and the icon are drawn pixel by pixel in `tools/`. A compressed block shows the game's own
texture of its block by name (no game texture is in the mod). Inspired by AllTheCompressed by the All The Mods
team; its code, art, names and numbers are not used (the blocks compressed are the game's own), and this mod
is not affiliated with or endorsed by All The Mods.

## License

MIT, see [LICENSE](LICENSE).
