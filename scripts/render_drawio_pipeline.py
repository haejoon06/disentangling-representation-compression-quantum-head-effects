from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figures"
WIDTH, HEIGHT = 1480, 760


def font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / name), size)


def rounded(draw, xy, fill, outline, radius=18, width=3):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def centered_lines(draw, xy, lines, sizes, colors=None, spacing=5):
    x0, y0, x1, y1 = xy
    fonts = [font(size, bold=index == 0) for index, size in enumerate(sizes)]
    boxes = [draw.textbbox((0, 0), line, font=f) for line, f in zip(lines, fonts)]
    heights = [box[3] - box[1] for box in boxes]
    total = sum(heights) + spacing * (len(lines) - 1)
    y = y0 + (y1 - y0 - total) / 2
    for index, (line, f, box, height) in enumerate(zip(lines, fonts, boxes, heights)):
        w = box[2] - box[0]
        color = (25, 25, 25) if colors is None else colors[index]
        draw.text((x0 + (x1 - x0 - w) / 2, y), line, font=f, fill=color)
        y += height + spacing


def arrow(draw, points, color="#355C7D", width=4):
    draw.line(points, fill=color, width=width, joint="curve")
    x, y = points[-1]
    px, py = points[-2]
    if abs(x - px) >= abs(y - py):
        sign = 1 if x > px else -1
        tip = [(x, y), (x - sign * 16, y - 9), (x - sign * 16, y + 9)]
    else:
        sign = 1 if y > py else -1
        tip = [(x, y), (x - 9, y - sign * 16), (x + 9, y - sign * 16)]
    draw.polygon(tip, fill=color)


def main():
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    top = [
        ((30, 55, 280, 143), ["Three visual domains", "CIFAR-10 · EuroSAT RGB · PathMNIST"]),
        ((330, 55, 580, 143), ["Frozen DINOv2 ViT-S/14", "deterministic 384D CLS embedding"]),
        ((610, 55, 860, 143), ["Cached representation", "identical vectors for every condition"]),
    ]
    for xy, lines in top:
        rounded(draw, xy, "#EAF2F8", "#355C7D")
        centered_lines(draw, xy, lines, [20, 12 if lines[0] == "Three visual domains" else 13])
    rounded(draw, (1060, 55, 1400, 143), "#F3F3F3", "#666666")
    centered_lines(draw, (1060, 55, 1400, 143), ["Full-space reference", "RBF-SVM on 384 dimensions"], [20, 15])
    arrow(draw, [(280, 99), (330, 99)])
    arrow(draw, [(580, 99), (610, 99)])
    arrow(draw, [(860, 99), (1060, 99)], color="#666666")

    draw.rounded_rectangle((220, 205, 1250, 370), radius=18, outline="#909090", width=2)
    draw.text((242, 218), "Representation bottleneck · identical six-dimensional budget", font=font(20, True), fill="#303030")
    reducer_boxes = [
        ((255, 265, 475, 335), ["PCA-6", "unsupervised variance"]),
        ((490, 265, 710, 335), ["LDA-6", "supervised linear separation"]),
        ((725, 265, 945, 335), ["NCA-6", "supervised metric learning"]),
        ((960, 265, 1180, 335), ["SLP-6", "learned supervised projection"]),
    ]
    for xy, lines in reducer_boxes:
        rounded(draw, xy, "#FFF4D6", "#B07D21")
        centered_lines(draw, xy, lines, [19, 13])
    arrow(draw, [(735, 143), (735, 205)])

    rounded(draw, (585, 410, 885, 485), "#E8F5EA", "#4D7A54")
    centered_lines(draw, (585, 410, 885, 485), ["Training-fitted angle scaling", "x̃ = π tanh(z)"], [19, 17])
    arrow(draw, [(735, 370), (735, 410)], color="#4D7A54")

    draw.rounded_rectangle((40, 535, 1180, 710), radius=18, outline="#909090", width=2)
    draw.text((62, 550), "Matched predictive heads · same samples, split, vectors, and seed", font=font(20, True), fill="#303030")
    head_boxes = [
        ((70, 610, 320, 675), ["Logistic regression"]),
        ((340, 610, 590, 675), ["RBF-SVM"]),
        ((610, 610, 860, 675), ["Parameter-matched MLP"]),
        ((880, 610, 1130, 675), ["Six-qubit VQC"]),
    ]
    for xy, lines in head_boxes:
        rounded(draw, xy, "#EEEAF7", "#705D8E")
        centered_lines(draw, xy, lines, [18 if lines[0] == "Parameter-matched MLP" else 19])
    arrow(draw, [(735, 485), (735, 535)], color="#705D8E")

    rounded(draw, (1210, 575, 1440, 670), "#EAF2F8", "#355C7D")
    centered_lines(draw, (1210, 575, 1440, 670), ["Validation-only selection", "10 paired seeds", "locked test evaluation"], [16, 14, 14])
    arrow(draw, [(1180, 622), (1210, 622)])

    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / "figure_01_pipeline.png", dpi=(300, 300))
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1480" height="760" viewBox="0 0 1480 760">
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="context-stroke"/></marker></defs>
<rect width="1480" height="760" fill="white"/>
<g font-family="Arial, sans-serif" text-anchor="middle" fill="#191919">
<g stroke="#355C7D" stroke-width="3" fill="#EAF2F8"><rect x="30" y="55" width="250" height="88" rx="18"/><rect x="330" y="55" width="250" height="88" rx="18"/><rect x="610" y="55" width="250" height="88" rx="18"/><rect x="1210" y="575" width="230" height="95" rx="18"/></g>
<g stroke="#666" stroke-width="3" fill="#F3F3F3"><rect x="1060" y="55" width="340" height="88" rx="18"/></g>
<g font-size="20" font-weight="700"><text x="155" y="91">Three visual domains</text><text x="455" y="91">Frozen DINOv2 ViT-S/14</text><text x="735" y="91">Cached representation</text><text x="1230" y="91">Full-space reference</text></g>
<g font-size="13"><text x="155" y="118" font-size="12">CIFAR-10 · EuroSAT RGB · PathMNIST</text><text x="455" y="118">deterministic 384D CLS embedding</text><text x="735" y="118">identical vectors for every condition</text><text x="1230" y="118" font-size="14">RBF-SVM on 384 dimensions</text></g>
<g fill="none" stroke="#909090" stroke-width="2" stroke-dasharray="8 6"><rect x="220" y="205" width="1030" height="165" rx="18"/><rect x="40" y="535" width="1140" height="175" rx="18"/></g>
<g text-anchor="start" font-size="20" font-weight="700"><text x="242" y="239">Representation bottleneck · identical six-dimensional budget</text><text x="62" y="570">Matched predictive heads · same samples, split, vectors, and seed</text></g>
<g stroke="#B07D21" stroke-width="3" fill="#FFF4D6"><rect x="255" y="265" width="220" height="70" rx="16"/><rect x="490" y="265" width="220" height="70" rx="16"/><rect x="725" y="265" width="220" height="70" rx="16"/><rect x="960" y="265" width="220" height="70" rx="16"/></g>
<g font-size="19" font-weight="700"><text x="365" y="296">PCA-6</text><text x="600" y="296">LDA-6</text><text x="835" y="296">NCA-6</text><text x="1070" y="296">SLP-6</text></g>
<g font-size="13"><text x="365" y="320">unsupervised variance</text><text x="600" y="320">supervised linear separation</text><text x="835" y="320">supervised metric learning</text><text x="1070" y="320">learned supervised projection</text></g>
<g stroke="#4D7A54" stroke-width="3" fill="#E8F5EA"><rect x="585" y="410" width="300" height="75" rx="18"/></g><text x="735" y="442" font-size="19" font-weight="700">Training-fitted angle scaling</text><text x="735" y="468" font-size="17">x̃ = π tanh(z)</text>
<g stroke="#705D8E" stroke-width="3" fill="#EEEAF7"><rect x="70" y="610" width="250" height="65" rx="16"/><rect x="340" y="610" width="250" height="65" rx="16"/><rect x="610" y="610" width="250" height="65" rx="16"/><rect x="880" y="610" width="250" height="65" rx="16"/></g>
<g font-size="19" font-weight="700"><text x="195" y="650">Logistic regression</text><text x="465" y="650">RBF-SVM</text><text x="735" y="650" font-size="18">Parameter-matched MLP</text><text x="1005" y="650">Six-qubit VQC</text></g>
<g font-size="16" font-weight="700"><text x="1325" y="609">Validation-only selection</text></g><g font-size="14"><text x="1325" y="636">10 paired seeds</text><text x="1325" y="657">locked test evaluation</text></g>
</g>
<g fill="none" stroke="#355C7D" stroke-width="4" marker-end="url(#arrow)"><path d="M280 99 H330"/><path d="M580 99 H610"/><path d="M860 99 H1060"/><path d="M735 143 V205"/><path d="M1180 622 H1210"/></g>
<g fill="none" stroke="#4D7A54" stroke-width="4" marker-end="url(#arrow)"><path d="M735 370 V410"/></g><g fill="none" stroke="#705D8E" stroke-width="4" marker-end="url(#arrow)"><path d="M735 485 V535"/></g>
</svg>'''
    (OUT / "figure_01_pipeline.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
