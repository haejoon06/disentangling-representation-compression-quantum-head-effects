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
        ((40, 55, 325, 143), ["Three visual domains", "CIFAR-10 · EuroSAT RGB · PathMNIST"]),
        ((385, 55, 670, 143), ["Frozen DINOv2 ViT-S/14", "deterministic 384D CLS embedding"]),
        ((730, 55, 1015, 143), ["Cached representation", "identical vectors for every condition"]),
    ]
    for xy, lines in top:
        rounded(draw, xy, "#EAF2F8", "#355C7D")
        centered_lines(draw, xy, lines, [22, 15 if lines[0] == "Three visual domains" else 17])
    rounded(draw, (1125, 40, 1425, 132), "#F3F3F3", "#666666")
    centered_lines(draw, (1125, 40, 1425, 132), ["Full-space reference", "RBF-SVM on 384 dimensions"], [22, 17])
    arrow(draw, [(325, 99), (385, 99)])
    arrow(draw, [(670, 99), (730, 99)])
    arrow(draw, [(1015, 99), (1060, 99), (1060, 86), (1125, 86)], color="#666666")

    draw.rounded_rectangle((40, 215, 1015, 380), radius=18, outline="#909090", width=2)
    draw.text((62, 226), "Representation bottleneck · identical six-dimensional budget", font=font(21, True), fill="#303030")
    reducer_boxes = [
        ((75, 270, 280, 344), ["PCA-6", "unsupervised variance"]),
        ((305, 270, 510, 344), ["LDA-6", "supervised linear separation"]),
        ((535, 270, 740, 344), ["NCA-6", "supervised metric learning"]),
        ((765, 270, 970, 344), ["SLP-6", "learned supervised projection"]),
    ]
    centers = []
    for xy, lines in reducer_boxes:
        rounded(draw, xy, "#FFF4D6", "#B07D21")
        centered_lines(draw, xy, lines, [21, 15])
        centers.append(((xy[0] + xy[2]) // 2, xy[1]))
    for cx, cy in centers:
        arrow(draw, [(872, 143), (872, 185), (cx, 185), (cx, cy)])

    rounded(draw, (370, 425, 690, 503), "#E8F5EA", "#4D7A54")
    centered_lines(draw, (370, 425, 690, 503), ["Training-fitted angle scaling", "x̃ = π tanh(z)"], [21, 19])
    arrow(draw, [(530, 380), (530, 425)], color="#4D7A54")

    draw.rounded_rectangle((40, 550, 1140, 710), radius=18, outline="#909090", width=2)
    draw.text((62, 561), "Matched predictive heads · same samples, split, vectors, and seed", font=font(21, True), fill="#303030")
    head_boxes = [
        ((75, 610, 305, 675), ["Logistic regression"]),
        ((335, 610, 565, 675), ["RBF-SVM"]),
        ((595, 610, 825, 675), ["Parameter-matched MLP"]),
        ((855, 610, 1085, 675), ["Six-qubit VQC"]),
    ]
    for xy, lines in head_boxes:
        rounded(draw, xy, "#EEEAF7", "#705D8E")
        centered_lines(draw, xy, lines, [20])
    arrow(draw, [(530, 503), (530, 530), (590, 530), (590, 550)], color="#705D8E")

    rounded(draw, (1190, 565, 1425, 690), "#EAF2F8", "#355C7D")
    centered_lines(draw, (1190, 565, 1425, 690), ["Validation-only selection", "10 paired seeds", "locked test evaluation"], [18, 17, 17])
    arrow(draw, [(1140, 630), (1190, 630)])

    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / "figure_01_pipeline.png", dpi=(300, 300))
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1480" height="760" viewBox="0 0 1480 760">
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="context-stroke"/></marker></defs>
<rect width="1480" height="760" fill="white"/>
<g font-family="Arial, sans-serif" text-anchor="middle" fill="#191919">
<g stroke="#355C7D" stroke-width="3" fill="#EAF2F8">
<rect x="40" y="55" width="285" height="88" rx="18"/><rect x="385" y="55" width="285" height="88" rx="18"/><rect x="730" y="55" width="285" height="88" rx="18"/><rect x="1190" y="565" width="235" height="125" rx="18"/>
</g>
<g stroke="#666" stroke-width="3" fill="#F3F3F3"><rect x="1125" y="40" width="300" height="92" rx="18"/></g>
<g font-size="22" font-weight="700"><text x="182" y="91">Three visual domains</text><text x="527" y="91">Frozen DINOv2 ViT-S/14</text><text x="872" y="91">Cached representation</text><text x="1275" y="77">Full-space reference</text></g>
<g font-size="17"><text x="182" y="119" font-size="15">CIFAR-10 · EuroSAT RGB · PathMNIST</text><text x="527" y="119">deterministic 384D CLS embedding</text><text x="872" y="119">identical vectors for every condition</text><text x="1275" y="105">RBF-SVM on 384 dimensions</text></g>
<g fill="none" stroke="#909090" stroke-width="2" stroke-dasharray="8 6"><rect x="40" y="215" width="975" height="165" rx="18"/><rect x="40" y="550" width="1100" height="160" rx="18"/></g>
<g text-anchor="start" font-size="21" font-weight="700"><text x="62" y="248">Representation bottleneck · identical six-dimensional budget</text><text x="62" y="583">Matched predictive heads · same samples, split, vectors, and seed</text></g>
<g stroke="#B07D21" stroke-width="3" fill="#FFF4D6"><rect x="75" y="270" width="205" height="74" rx="16"/><rect x="305" y="270" width="205" height="74" rx="16"/><rect x="535" y="270" width="205" height="74" rx="16"/><rect x="765" y="270" width="205" height="74" rx="16"/></g>
<g font-size="21" font-weight="700"><text x="177" y="301">PCA-6</text><text x="407" y="301">LDA-6</text><text x="637" y="301">NCA-6</text><text x="867" y="301">SLP-6</text></g>
<g font-size="15"><text x="177" y="326">unsupervised variance</text><text x="407" y="326">supervised linear separation</text><text x="637" y="326">supervised metric learning</text><text x="867" y="326">learned supervised projection</text></g>
<g stroke="#4D7A54" stroke-width="3" fill="#E8F5EA"><rect x="370" y="425" width="320" height="78" rx="18"/></g><text x="530" y="458" font-size="21" font-weight="700">Training-fitted angle scaling</text><text x="530" y="485" font-size="19">x̃ = π tanh(z)</text>
<g stroke="#705D8E" stroke-width="3" fill="#EEEAF7"><rect x="75" y="610" width="230" height="65" rx="16"/><rect x="335" y="610" width="230" height="65" rx="16"/><rect x="595" y="610" width="230" height="65" rx="16"/><rect x="855" y="610" width="230" height="65" rx="16"/></g>
<g font-size="20" font-weight="700"><text x="190" y="650">Logistic regression</text><text x="450" y="650">RBF-SVM</text><text x="710" y="650">Parameter-matched MLP</text><text x="970" y="650">Six-qubit VQC</text></g>
<g font-size="18" font-weight="700"><text x="1307" y="606">Validation-only selection</text></g><g font-size="17"><text x="1307" y="637">10 paired seeds</text><text x="1307" y="666">locked test evaluation</text></g>
</g>
<g fill="none" stroke="#355C7D" stroke-width="4" marker-end="url(#arrow)"><path d="M325 99 H385"/><path d="M670 99 H730"/><path d="M1015 99 H1060 V86 H1125"/><path d="M872 143 V185 H177 V270"/><path d="M872 143 V185 H407 V270"/><path d="M872 143 V185 H637 V270"/><path d="M872 143 V270"/><path d="M1140 630 H1190"/></g>
<g fill="none" stroke="#4D7A54" stroke-width="4" marker-end="url(#arrow)"><path d="M530 380 V425"/></g><g fill="none" stroke="#705D8E" stroke-width="4" marker-end="url(#arrow)"><path d="M530 503 V530 H590 V550"/></g>
</svg>'''
    (OUT / "figure_01_pipeline.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
