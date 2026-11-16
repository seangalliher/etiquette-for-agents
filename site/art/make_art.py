"""Generates the site's retro robot illustrations as SVG files in this folder.

One robot, drawn from the same parts in every picture; only the pose and props
change. Run: python site/art/make_art.py
"""

from pathlib import Path

INK, STEEL, SHADE, CREAM, RUST, TEAL, DARK, PEACH = (
    "#3b2e2a", "#c9d6d0", "#a9bdb5", "#f4ecdc", "#b7410e", "#4f8a83", "#3b2e2a", "#f2c8a8")

STYLE = f"""<defs><style>
.ink{{stroke:{INK};stroke-width:3;stroke-linejoin:round;stroke-linecap:round}}
.steel{{fill:{STEEL}}}.shade{{fill:{SHADE}}}.cream{{fill:{CREAM}}}.rust{{fill:{RUST}}}
.teal{{fill:{TEAL}}}.dark{{fill:{DARK}}}.none{{fill:none}}
</style></defs>"""


def burst(cx, cy):
    rays = [(0, -132), (112, -54), (-112, -54), (106, 60), (-106, 60)]
    lines = "".join(f'<line x1="{cx}" y1="{cy}" x2="{cx + dx}" y2="{cy + dy}"/>' for dx, dy in rays)
    return (f'<g stroke="{RUST}" stroke-width="3" stroke-linecap="round" opacity="0.35">{lines}</g>'
            f'<circle cx="{cx}" cy="{cy}" r="104" fill="none" stroke="{TEAL}" stroke-width="2" '
            f'stroke-dasharray="2 9" opacity="0.6"/>')


def arm(d):
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="17" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{STEEL}" stroke-width="11" stroke-linecap="round"/>')


def hand(x, y, r=9):
    return f'<circle class="ink cream" cx="{x}" cy="{y}" r="{r}"/>'


def legs():
    return ('<ellipse cx="130" cy="282" rx="70" ry="9" fill="#3b2e2a" opacity="0.15"/>'
            '<rect class="ink steel" x="102" y="214" width="20" height="50" rx="6"/>'
            '<rect class="ink steel" x="138" y="214" width="20" height="50" rx="6"/>'
            '<path class="ink dark" d="M92 278 Q92 262 112 262 Q126 262 126 278 Z"/>'
            '<path class="ink dark" d="M134 278 Q134 262 148 262 Q168 262 168 278 Z"/>')


def body():
    return ('<rect class="ink steel" x="76" y="116" width="108" height="104" rx="20"/>'
            '<rect class="shade" x="80" y="196" width="100" height="20" rx="10"/>'
            '<rect class="ink cream" x="96" y="134" width="68" height="46" rx="8"/>'
            '<circle class="ink cream" cx="114" cy="157" r="11"/>'
            '<line class="ink" x1="114" y1="157" x2="120" y2="149"/>'
            f'<circle class="rust" cx="140" cy="148" r="4.5"/><circle class="teal" cx="152" cy="148" r="4.5"/>'
            '<rect class="dark" x="136" y="160" width="20" height="3" rx="1.5"/>'
            '<rect class="dark" x="136" y="167" width="14" height="3" rx="1.5"/>'
            '<circle class="dark" cx="90" cy="206" r="2.5"/><circle class="dark" cx="170" cy="206" r="2.5"/>')


def neck(tie=RUST):
    return ('<rect class="ink shade" x="118" y="100" width="24" height="18" rx="3"/>'
            f'<path class="ink" fill="{tie}" d="M130 114 L108 104 Q104 103 104 107 L104 123 Q104 127 108 126 Z"/>'
            f'<path class="ink" fill="{tie}" d="M130 114 L152 104 Q156 103 156 107 L156 123 Q156 127 152 126 Z"/>'
            '<rect class="ink dark" x="124" y="108" width="12" height="13" rx="3"/>'
            f'<circle cx="130" cy="114.5" r="2.4" fill="{PEACH}"/>')


def head(tilt=0, look=(2, 2), glasses=False, lids=False):
    lx, ly = look
    eyes = (f'<circle class="ink cream" cx="111" cy="64" r="12"/><circle class="ink cream" cx="149" cy="64" r="12"/>'
            f'<circle class="dark" cx="{111 + lx}" cy="{64 + ly}" r="5"/><circle class="dark" cx="{149 + lx}" cy="{64 + ly}" r="5"/>')
    if lids:  # half-lowered lids: a sheepish look
        eyes += ''.join(f'<path class="ink steel" d="M{x - 13} 64 A13 13 0 0 1 {x + 13} 64 Z"/>' for x in (111, 149))
    if glasses:
        eyes += (f'<circle cx="111" cy="64" r="15" fill="none" stroke="{RUST}" stroke-width="3"/>'
                 f'<circle cx="149" cy="64" r="15" fill="none" stroke="{RUST}" stroke-width="3"/>'
                 f'<line x1="126" y1="64" x2="134" y2="64" stroke="{RUST}" stroke-width="3"/>')
    return (f'<g transform="rotate({tilt} 130 74)">'
            '<line class="ink" x1="130" y1="38" x2="130" y2="16"/><circle class="ink rust" cx="130" cy="13" r="7"/>'
            '<rect class="ink steel" x="86" y="36" width="88" height="66" rx="16"/>'
            '<circle class="ink teal" cx="84" cy="70" r="7"/><circle class="ink teal" cx="176" cy="70" r="7"/>'
            + eyes +
            '<rect class="ink cream" x="110" y="84" width="40" height="10" rx="4"/>'
            '<g class="ink"><line x1="120" y1="84" x2="120" y2="94"/><line x1="130" y1="84" x2="130" y2="94"/>'
            '<line x1="140" y1="84" x2="140" y2="94"/></g></g>')


HANG_LEFT = arm("M84 132 C62 150 58 182 66 204") + '<path class="ink cream" d="M58 204 Q66 222 76 206 Q70 214 66 208 Z"/>'
CHEST_RIGHT = arm("M176 132 C200 146 196 172 166 176") + hand(160, 176)


def robot(front_arm, back_arm=HANG_LEFT, tie=RUST, **head_kw):
    return legs() + back_arm + body() + front_arm + neck(tie) + head(**head_kw)


def svg(w, label, *parts):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 300" role="img" aria-label="{label}">'
            + STYLE + "".join(parts) + "</svg>\n")


CUP = (f'<path class="ink cream" d="M-12 -18 L12 -18 L9 -2 Q0 3 -9 -2 Z"/>'
       f'<rect x="-11" y="-14" width="22" height="3" fill="{TEAL}"/>'
       f'<path d="M11 -14 Q19 -13 17 -7 Q16 -3 10 -5" fill="none" stroke="{INK}" stroke-width="3"/>')

ART = {
    "home": svg(260, "A friendly 1950s-style robot in a bow tie, bowing politely",
                burst(130, 150), robot(CHEST_RIGHT, tilt=-8)),

    "part1": svg(260, "The robot reading a small book through rust-rimmed glasses",
                 burst(130, 150),
                 legs(), arm("M84 132 C70 160 92 178 108 176"), body(),
                 neck(), head(tilt=4, look=(0, 5), glasses=True),
                 f'<path class="ink rust" d="M92 150 L130 158 L168 150 L168 190 L130 198 L92 190 Z"/>',
                 f'<path class="ink cream" d="M96 152 L130 160 L130 194 L96 186 Z"/>',
                 f'<path class="ink cream" d="M164 152 L130 160 L130 194 L164 186 Z"/>',
                 ''.join(f'<line x1="102" y1="{y}" x2="124" y2="{y + 5}" stroke="{SHADE}" stroke-width="2"/>' for y in (164, 171, 178)),
                 ''.join(f'<line x1="136" y1="{y + 5}" x2="158" y2="{y}" stroke="{SHADE}" stroke-width="2"/>' for y in (164, 171, 178)),
                 arm("M176 132 C190 160 168 178 152 176"), hand(104, 182), hand(156, 182)),

    "part2": svg(260, "The robot offering a cup of tea on a saucer",
                 burst(130, 150),
                 robot(arm("M176 132 C204 140 214 156 220 170") + hand(220, 174), tilt=6, look=(4, 2)),
                 '<ellipse class="ink cream" cx="222" cy="166" rx="24" ry="6"/>',
                 f'<g transform="translate(222 164)">{CUP}</g>',
                 f'<g fill="none" stroke="{TEAL}" stroke-width="2.5" stroke-linecap="round">'
                 '<path d="M216 140 q-5 -6 0 -12 q5 -6 0 -12"/><path d="M228 140 q-5 -6 0 -12 q5 -6 0 -12"/></g>'),

    "part3": svg(270, "The robot carefully filing a folder in an open filing cabinet",
                 burst(135, 150),
                 '<g transform="translate(-34 0)">',
                 robot(arm("M176 132 C200 140 206 156 210 168") + hand(212, 170), tilt=5, look=(5, 4)),
                 '</g>',
                 '<rect class="ink teal" x="196" y="150" width="66" height="132" rx="4"/>',
                 ''.join(f'<rect class="ink" fill="#5f9a93" x="202" y="{y}" width="54" height="34" rx="3"/>'
                         f'<rect class="ink cream" x="221" y="{y + 13}" width="16" height="7" rx="2"/>'
                         for y in (198, 240)),
                 '<path class="ink" fill="#5f9a93" d="M164 160 L256 160 L256 192 L164 192 Z"/>',
                 '<path class="ink cream" d="M170 160 L176 148 L190 148 L194 154 L232 154 L232 160 Z"/>',
                 '<path class="ink rust" d="M168 150 L176 132 L196 136 L190 158 Z"/>',
                 '<rect class="ink cream" x="200" y="172" width="16" height="7" rx="2"/>'),

    "part4": svg(380, "Two robots bowing politely to each other",
                 burst(190, 150),
                 '<g transform="translate(14 46) scale(0.8)">', robot(CHEST_RIGHT, tilt=10, look=(5, 3)), '</g>',
                 '<g transform="translate(370 46) scale(-0.8 0.8)">', robot(CHEST_RIGHT, tie=TEAL, tilt=10, look=(5, 3)), '</g>'),

    "part5": svg(260, "The robot raising a hand beside a spilled teacup, owning the mistake",
                 burst(130, 150),
                 f'<ellipse cx="46" cy="280" rx="34" ry="7" fill="{TEAL}" opacity="0.55"/>',
                 '<g transform="translate(46 268) rotate(-100) scale(1.4)">', CUP, '</g>',
                 robot(arm("M176 132 C204 120 212 96 206 76") + hand(206, 70, 11)
                       + f'<g class="ink">' + "".join(f'<line x1="{x}" y1="62" x2="{x}" y2="52"/>' for x in (200, 206, 212)) + '</g>',
                       tilt=-6, look=(-3, 4), lids=True),
                 f'<path d="M180 40 q5 9 0 13 q-5 -4 0 -13 Z" fill="{TEAL}" stroke="{INK}" stroke-width="2"/>'),

    "part6": svg(320, "The robot weighing a hard call on a pair of balance scales",
                 burst(130, 150),
                 robot(arm("M176 132 C210 118 230 84 234 54") + hand(236, 48),
                       back_arm=arm("M84 132 C62 124 76 104 96 106") + hand(98, 106),
                       tilt=-10, look=(4, -3)),
                 f'<g transform="translate(36 -12) rotate(-7 200 60)">'
                 f'<line x1="152" y1="58" x2="248" y2="58" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
                 f'<path class="ink rust" d="M200 48 L207 60 L193 60 Z"/>'
                 + "".join(f'<line x1="{x}" y1="58" x2="{x - 14}" y2="96" stroke="{INK}" stroke-width="2"/>'
                           f'<line x1="{x}" y1="58" x2="{x + 14}" y2="96" stroke="{INK}" stroke-width="2"/>'
                           f'<path class="ink cream" d="M{x - 20} 96 Q{x} 112 {x + 20} 96 Z"/>' for x in (152, 248))
                 + '</g>'),
}

if __name__ == "__main__":
    here = Path(__file__).parent
    for name, text in ART.items():
        (here / f"{name}.svg").write_text(text, encoding="utf-8")
    print("wrote", ", ".join(ART))
