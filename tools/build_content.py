#!/usr/bin/env python3
"""Builds Vast Compressed, a content mod for Horizon: blocks packed nine at a time, from I (9 blocks) to IX
(387,420,489 blocks), each one back to nine of the tier below.

Inspired by AllTheCompressed, but nothing here comes from its jar: the list of blocks is the game's own, the
overlays that mark each tier are drawn below pixel by pixel, the names and numbers are this mod's. A compressed
block draws the game's own texture of its block (never copied, only named) under the tier's overlay.
Usage: build_content.py <output dir>   (writes <output dir>/vastcompressed)
"""
import json
import shutil
import struct
import sys
import zlib
from pathlib import Path

NS = "vastcompressed"
VERSION = "0.1.0"
TIERS = 9
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]

# ---- the blocks ----------------------------------------------------------------

# Families: the template whose behaviour the block takes (a plain one, so a compressed sand doesn't fall and a
# compressed dirt can't be tilled), the tool that mines it and whether it drops without that tool.
FAMILIES = {
    "stone": ("minecraft:stone", "pickaxe", True),
    "metal": ("minecraft:iron_block", "pickaxe", True),
    "soil": ("minecraft:clay", "shovel", False),
    "plant": ("minecraft:clay", "hoe", False),
    "wood": ("minecraft:oak_planks", "axe", False),
    "glass": ("minecraft:glass", None, False),
    # Its own block: light (glowstone, magma), slipperiness (blue ice) or stickiness (honey) come with it.
    "self": (None, "pickaxe", False),
}

# id, family, hardness, blast resistance, textures (all; or up, down, side), english, portuguese, pt gender
# (m, f, mp, fp), tool tier tag. Textures are the game's (`minecraft:block/<name>`).
M, F, MP, FP = "m", "f", "mp", "fp"
BLOCKS = [
    # stone
    ("cobblestone", "stone", 2.0, 6.0, None, "Cobblestone", "Pedregulho", M, None),
    ("stone", "stone", 1.5, 6.0, None, "Stone", "Pedra", F, None),
    ("smooth_stone", "stone", 2.0, 6.0, None, "Smooth Stone", "Pedra Lisa", F, None),
    ("andesite", "stone", 1.5, 6.0, None, "Andesite", "Andesito", M, None),
    ("diorite", "stone", 1.5, 6.0, None, "Diorite", "Diorito", M, None),
    ("granite", "stone", 1.5, 6.0, None, "Granite", "Granito", M, None),
    ("tuff", "stone", 1.5, 6.0, None, "Tuff", "Tufo", M, None),
    ("calcite", "stone", 0.75, 0.75, None, "Calcite", "Calcita", F, None),
    ("deepslate", "stone", 3.0, 6.0, ("deepslate_top", "deepslate_top", "deepslate"), "Deepslate", "Ardósia", F, None),
    ("cobbled_deepslate", "stone", 3.5, 6.0, None, "Cobbled Deepslate", "Pedregulho de Ardósia", M, None),
    ("dripstone_block", "stone", 1.5, 1.0, None, "Dripstone", "Espeleotema", M, None),
    ("bricks", "stone", 2.0, 6.0, None, "Bricks", "Tijolos", MP, None),
    ("terracotta", "stone", 1.25, 4.2, None, "Terracotta", "Terracota", F, None),
    ("netherrack", "stone", 0.4, 0.4, None, "Netherrack", "Netherrack", M, None),
    ("blackstone", "stone", 1.5, 6.0, ("blackstone_top", "blackstone_top", "blackstone"), "Blackstone", "Pedra-Negra", F, None),
    ("basalt", "stone", 1.25, 4.2, ("basalt_top", "basalt_top", "basalt_side"), "Basalt", "Basalto", M, None),
    ("end_stone", "stone", 3.0, 9.0, None, "End Stone", "Pedra do End", F, None),
    ("obsidian", "stone", 50.0, 1200.0, None, "Obsidian", "Obsidiana", F, "minecraft:needs_diamond_tool"),
    ("amethyst_block", "stone", 1.5, 1.5, None, "Amethyst", "Ametista", F, None),
    ("quartz_block", "stone", 0.8, 0.8, ("quartz_block_top", "quartz_block_bottom", "quartz_block_side"), "Quartz", "Quartzo", M, None),
    ("bone_block", "stone", 2.0, 2.0, ("bone_block_top", "bone_block_top", "bone_block_side"), "Bone", "Osso", M, None),
    ("packed_mud", "stone", 1.0, 3.0, None, "Packed Mud", "Lama Compacta", F, None),
    # soil
    ("dirt", "soil", 0.5, 0.5, None, "Dirt", "Terra", F, None),
    ("podzol", "soil", 0.5, 0.5, ("podzol_top", "dirt", "podzol_side"), "Podzol", "Podzol", M, None),
    ("mycelium", "soil", 0.6, 0.6, ("mycelium_top", "dirt", "mycelium_side"), "Mycelium", "Micélio", M, None),
    ("mud", "soil", 0.5, 0.5, None, "Mud", "Lama", F, None),
    ("clay", "soil", 0.6, 0.6, None, "Clay", "Argila", F, None),
    ("sand", "soil", 0.5, 0.5, None, "Sand", "Areia", F, None),
    ("red_sand", "soil", 0.5, 0.5, None, "Red Sand", "Areia Vermelha", F, None),
    ("gravel", "soil", 0.6, 0.6, None, "Gravel", "Cascalho", M, None),
    ("soul_sand", "soil", 0.5, 0.5, None, "Soul Sand", "Areia das Almas", F, None),
    ("soul_soil", "soil", 0.5, 0.5, None, "Soul Soil", "Solo das Almas", M, None),
    ("snow_block", "soil", 0.2, 0.2, ("snow",), "Snow", "Neve", F, None),
    # plants
    ("moss_block", "plant", 0.1, 0.1, None, "Moss", "Musgo", M, None),
    ("nether_wart_block", "plant", 1.0, 1.0, None, "Nether Wart", "Fungo do Nether", M, None),
    ("warped_wart_block", "plant", 1.0, 1.0, None, "Warped Wart", "Fungo Distorcido", M, None),
    ("hay_block", "plant", 0.5, 0.5, ("hay_block_top", "hay_block_top", "hay_block_side"), "Hay", "Feno", M, None),
    ("dried_kelp_block", "plant", 0.5, 2.5, ("dried_kelp_top", "dried_kelp_bottom", "dried_kelp_side"), "Dried Kelp", "Alga Seca", F, None),
    ("sponge", "plant", 0.6, 0.6, None, "Sponge", "Esponja", F, None),
    # wood
    ("oak_log", "wood", 2.0, 2.0, ("oak_log_top", "oak_log_top", "oak_log"), "Oak Log", "Tronco de Carvalho", M, None),
    ("spruce_log", "wood", 2.0, 2.0, ("spruce_log_top", "spruce_log_top", "spruce_log"), "Spruce Log", "Tronco de Pinheiro", M, None),
    ("birch_log", "wood", 2.0, 2.0, ("birch_log_top", "birch_log_top", "birch_log"), "Birch Log", "Tronco de Bétula", M, None),
    ("jungle_log", "wood", 2.0, 2.0, ("jungle_log_top", "jungle_log_top", "jungle_log"), "Jungle Log", "Tronco da Selva", M, None),
    ("acacia_log", "wood", 2.0, 2.0, ("acacia_log_top", "acacia_log_top", "acacia_log"), "Acacia Log", "Tronco de Acácia", M, None),
    ("dark_oak_log", "wood", 2.0, 2.0, ("dark_oak_log_top", "dark_oak_log_top", "dark_oak_log"), "Dark Oak Log", "Tronco de Carvalho-Escuro", M, None),
    ("mangrove_log", "wood", 2.0, 2.0, ("mangrove_log_top", "mangrove_log_top", "mangrove_log"), "Mangrove Log", "Tronco de Mangue", M, None),
    ("cherry_log", "wood", 2.0, 2.0, ("cherry_log_top", "cherry_log_top", "cherry_log"), "Cherry Log", "Tronco de Cerejeira", M, None),
    ("pale_oak_log", "wood", 2.0, 2.0, ("pale_oak_log_top", "pale_oak_log_top", "pale_oak_log"), "Pale Oak Log", "Tronco de Carvalho-Pálido", M, None),
    ("oak_planks", "wood", 2.0, 3.0, None, "Oak Planks", "Tábuas de Carvalho", FP, None),
    ("spruce_planks", "wood", 2.0, 3.0, None, "Spruce Planks", "Tábuas de Pinheiro", FP, None),
    ("birch_planks", "wood", 2.0, 3.0, None, "Birch Planks", "Tábuas de Bétula", FP, None),
    ("jungle_planks", "wood", 2.0, 3.0, None, "Jungle Planks", "Tábuas da Selva", FP, None),
    ("acacia_planks", "wood", 2.0, 3.0, None, "Acacia Planks", "Tábuas de Acácia", FP, None),
    ("dark_oak_planks", "wood", 2.0, 3.0, None, "Dark Oak Planks", "Tábuas de Carvalho-Escuro", FP, None),
    ("mangrove_planks", "wood", 2.0, 3.0, None, "Mangrove Planks", "Tábuas de Mangue", FP, None),
    ("cherry_planks", "wood", 2.0, 3.0, None, "Cherry Planks", "Tábuas de Cerejeira", FP, None),
    ("pale_oak_planks", "wood", 2.0, 3.0, None, "Pale Oak Planks", "Tábuas de Carvalho-Pálido", FP, None),
    ("pumpkin", "wood", 1.0, 1.0, ("pumpkin_top", "pumpkin_top", "pumpkin_side"), "Pumpkin", "Abóbora", F, None),
    ("melon", "wood", 1.0, 1.0, ("melon_top", "melon_top", "melon_side"), "Melon", "Melancia", F, None),
    # metals and gems
    ("coal_block", "metal", 5.0, 6.0, None, "Coal", "Carvão", M, None),
    ("iron_block", "metal", 5.0, 6.0, None, "Iron", "Ferro", M, "minecraft:needs_stone_tool"),
    ("gold_block", "metal", 3.0, 6.0, None, "Gold", "Ouro", M, "minecraft:needs_iron_tool"),
    ("copper_block", "metal", 3.0, 6.0, None, "Copper", "Cobre", M, "minecraft:needs_stone_tool"),
    ("raw_iron_block", "metal", 5.0, 6.0, None, "Raw Iron", "Ferro Bruto", M, "minecraft:needs_stone_tool"),
    ("raw_gold_block", "metal", 5.0, 6.0, None, "Raw Gold", "Ouro Bruto", M, "minecraft:needs_iron_tool"),
    ("raw_copper_block", "metal", 5.0, 6.0, None, "Raw Copper", "Cobre Bruto", M, "minecraft:needs_stone_tool"),
    ("redstone_block", "metal", 5.0, 6.0, None, "Redstone", "Redstone", F, None),
    ("lapis_block", "metal", 3.0, 3.0, None, "Lapis Lazuli", "Lápis-Lazúli", M, "minecraft:needs_stone_tool"),
    ("diamond_block", "metal", 5.0, 6.0, None, "Diamond", "Diamante", M, "minecraft:needs_iron_tool"),
    ("emerald_block", "metal", 5.0, 6.0, None, "Emerald", "Esmeralda", F, "minecraft:needs_iron_tool"),
    ("netherite_block", "metal", 50.0, 1200.0, None, "Netherite", "Netherita", F, "minecraft:needs_diamond_tool"),
    # their own behaviour
    ("glass", "glass", 0.3, 0.3, None, "Glass", "Vidro", M, None),
    ("glowstone", "self", 0.3, 0.3, None, "Glowstone", "Pedra Luminosa", F, None),
    ("magma_block", "self", 0.5, 0.5, ("magma",), "Magma", "Magma", M, None),
    ("blue_ice", "self", 2.8, 2.8, None, "Blue Ice", "Gelo Azul", M, None),
    ("honeycomb_block", "plant", 0.6, 0.6, None, "Honeycomb", "Favo de Mel", M, None),
]
COLORS = [
    ("white", "White", "Branco"), ("light_gray", "Light Gray", "Cinza-Claro"), ("gray", "Gray", "Cinza"),
    ("black", "Black", "Preto"), ("brown", "Brown", "Marrom"), ("red", "Red", "Vermelho"), ("orange", "Orange", "Laranja"),
    ("yellow", "Yellow", "Amarelo"), ("lime", "Lime", "Verde-Limão"), ("green", "Green", "Verde"), ("cyan", "Cyan", "Ciano"),
    ("light_blue", "Light Blue", "Azul-Claro"), ("blue", "Blue", "Azul"), ("purple", "Purple", "Roxo"),
    ("magenta", "Magenta", "Magenta"), ("pink", "Pink", "Rosa"),
]
for color, en, pt in COLORS:
    BLOCKS.append((f"{color}_concrete", "stone", 1.8, 1.8, None, f"{en} Concrete", f"Concreto {pt}", M, None))

PT_ADJ = {M: "Compactado", F: "Compactada", MP: "Compactados", FP: "Compactadas"}

# How much harder each tier is than the one below it, to mine and to blow up.
HARDER = 0.25

# ---- the overlays (drawn here) ---------------------------------------------------

# Three bands of three tiers, each band its own metal: steel, brass, then a deep violet. Within a band the
# second tier adds corner brackets and the third rivets in the middle of each side.
BANDS = [
    ((0x22, 0x26, 0x2C), (0x8C, 0x96, 0xA2)),
    ((0x3A, 0x26, 0x0E), (0xE0, 0xA2, 0x34)),
    ((0x24, 0x10, 0x34), (0xB8, 0x62, 0xE8)),
]


def overlay(tier):
    """Tier (1..9)'s 16x16 overlay: opaque pixels only, the rest clear (the block is drawn as cutout)."""
    dark, light = BANDS[(tier - 1) // 3]
    mid = tuple((d + l) // 2 for d, l in zip(dark, light))
    step = (tier - 1) % 3
    clear = (0, 0, 0, 0)
    px = [[clear] * 16 for _ in range(16)]

    def put(x, y, c):
        px[y][x] = (*c, 255)

    # The frame: a dark rim, and inside it a bevel lit on the top and left, shaded on the bottom and right.
    for i in range(16):
        for x, y in ((i, 0), (i, 15), (0, i), (15, i)):
            put(x, y, dark)
    for i in range(1, 15):
        put(i, 1, light)
        put(1, i, light)
        put(i, 14, mid)
        put(14, i, mid)
    put(14, 1, mid)
    put(1, 14, mid)
    if step >= 1:
        # A square plate in each corner, lit like the frame.
        for x, y in ((2, 2), (12, 2), (2, 12), (12, 12)):
            put(x, y, light)
            put(x + 1, y, light)
            put(x, y + 1, light)
            put(x + 1, y + 1, mid)
    if step >= 2:
        # A rivet in the middle of each side, its shadow under it.
        for x, y in ((7, 2), (8, 2), (7, 12), (8, 12), (2, 7), (2, 8), (12, 7), (12, 8)):
            put(x, y, light)
        for x, y in ((7, 3), (8, 3), (7, 13), (8, 13), (3, 7), (3, 8), (13, 7), (13, 8)):
            put(x, y, dark)
    return px


def png(pixels):
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in pixels)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", len(pixels[0]), len(pixels), 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# ---- the mod --------------------------------------------------------------------

def model(textures, tier):
    """The game's block (each face its own texture) and the tier's overlay over it."""
    up, down, side = textures
    faces = {"up": "#up", "down": "#down", "north": "#side", "south": "#side", "east": "#side", "west": "#side"}
    return {
        "parent": "minecraft:block/block",
        "render_type": "minecraft:cutout",
        "textures": {"particle": f"minecraft:block/{side}", "up": f"minecraft:block/{up}", "down": f"minecraft:block/{down}",
                     "side": f"minecraft:block/{side}", "overlay": f"{NS}:block/tier_{tier}"},
        "elements": [
            {"from": [0, 0, 0], "to": [16, 16, 16],
             "faces": {f: {"texture": t, "cullface": f} for f, t in faces.items()}},
            {"from": [0, 0, 0], "to": [16, 16, 16],
             "faces": {f: {"texture": "#overlay", "cullface": f} for f in faces}},
        ],
    }


def build(out):
    files, tags = {}, {}
    lang_en = {f"{NS}.blocks": "%s blocks"}
    lang_pt = {f"{NS}.blocks": "%s blocos"}
    items = []

    def tag(registry, name, value):
        tags.setdefault((registry, name), []).append(value)

    for tier in range(1, TIERS + 1):
        files[f"assets/{NS}/textures/block/tier_{tier}.png"] = png(overlay(tier))
    for base, family, hardness, resistance, textures, en, pt, gender, needs in BLOCKS:
        template, tool, requires_tool = FAMILIES[family]
        template = template or f"minecraft:{base}"
        textures = textures or (base,)
        if len(textures) == 1:
            textures = textures * 3
        below = f"minecraft:{base}"
        for tier in range(1, TIERS + 1):
            name = f"{base}_{tier}"
            full = f"{NS}:{name}"
            scale = 1.0 + HARDER * tier
            props = {"hardness": round(hardness * scale, 3), "explosion_resistance": round(resistance * scale, 2),
                     "sounds": f"minecraft:{base}"}
            if requires_tool:
                props["requires_tool"] = True
            files[f"data/{NS}/horizon/block/{name}.json"] = {
                "template": template, "item": True, "properties": props,
                "components": {"minecraft:lore": [{"translate": f"{NS}.blocks", "with": [f"{9 ** tier:,}"],
                                                   "color": "gray", "italic": False}]}}
            files[f"assets/{NS}/blockstates/{name}.json"] = {"variants": {"": {"model": f"{NS}:block/{name}"}}}
            files[f"assets/{NS}/models/block/{name}.json"] = model(textures, tier)
            files[f"assets/{NS}/items/{name}.json"] = {"model": {"type": "minecraft:model", "model": f"{NS}:block/{name}"}}
            files[f"data/{NS}/loot_table/blocks/{name}.json"] = {
                "type": "minecraft:block", "random_sequence": f"{NS}:blocks/{name}",
                "pools": [{"bonus_rolls": 0.0, "rolls": 1.0, "entries": [{"type": "minecraft:item", "name": full}],
                           "conditions": [{"condition": "minecraft:survives_explosion"}]}]}
            files[f"data/{NS}/recipe/compress/{name}.json"] = {
                "type": "minecraft:crafting_shaped", "category": "building", "key": {"#": below},
                "pattern": ["###", "###", "###"], "result": {"id": full}}
            files[f"data/{NS}/recipe/decompress/{name}.json"] = {
                "type": "minecraft:crafting_shapeless", "category": "building", "ingredients": [full],
                "result": {"count": 9, "id": below}}
            lang_en[f"block.{NS}.{name}"] = f"Compressed {en} {ROMAN[tier - 1]}"
            lang_pt[f"block.{NS}.{name}"] = f"{pt} {PT_ADJ[gender]} {ROMAN[tier - 1]}"
            if tool:
                tag("block", f"minecraft:mineable/{tool}", full)
            if needs:
                tag("block", needs, full)
            tag("block", f"{NS}:compressed", full)
            tag("item", f"{NS}:compressed", full)
            tag("item", f"{NS}:compressed/{base}", full)
            items.append(full)
            below = full
    for (registry, name), values in tags.items():
        tns, path = name.split(":")
        files[f"data/{tns}/tags/{registry}/{path}.json"] = {"values": sorted(set(values))}
    files[f"data/{NS}/horizon/creative_tab/main.json"] = {"title": "Vast Compressed", "icon": f"{NS}:cobblestone_3",
                                                          "items": items}
    files[f"assets/{NS}/lang/en_us.json"] = dict(sorted(lang_en.items()))
    files[f"assets/{NS}/lang/pt_br.json"] = dict(sorted(lang_pt.items()))

    out = Path(out) / NS
    if out.exists():
        shutil.rmtree(out)
    for path, value in files.items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):
            target.write_bytes(value)
        else:
            target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    (out / "horizon-mod.toml").write_text(
        f'id = "{NS}"\nname = "Vast Compressed"\nversion = "{VERSION}"\n'
        'description = "Blocks packed nine at a time, from I (9 blocks) to IX (387,420,489), and back."\n'
        'authors = ["voltzz900"]\napi = "0.2"\nside = "both"\ncapabilities = ["registries"]\n')
    print(f"{NS}: {len(BLOCKS)} blocks x {TIERS} tiers = {len(items)} blocks, {2 * len(items)} recipes, {len(files) + 1} files")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "build")
