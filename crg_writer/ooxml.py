"""A small Word (.docx, Office Open XML) writer and reader — standard library only.

The writer produces native, editable documents: real headings (so Word builds the table of contents),
real tables with a repeating header row, page numbers, a header and footer, document properties, and
hidden bookmarks that carry the identifier of each statement so that an edited copy can be read back.
The reader returns the body paragraphs with their bookmarks and style, the core properties, and refuses
macro-enabled or oversized archives.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
CM = 567                                    # twips per centimetre
INK, ACCENT, RED, GREY = "1F2A37", "0B4F6C", "B42318", "5F6B76"
PH_RE = re.compile(r"\[(DECISION|DÉCISION|ROLE|RÔLE|VALUE|VALEUR|DATE|SOURCE|APPROVER|APPROBATEUR|TECHNICAL_DETAIL|DÉTAIL_TECHNIQUE)\s*:\s*[^\]]+\]")


def _x(s) -> str:
    return escape("" if s is None else str(s), {'"': "&quot;"})


def bookmark(kind: str, ident: str) -> str:
    """Hidden Word bookmark name (leading underscore = hidden in Word's dialog): letters, digits, underscores."""
    return ("_crg" + kind + "_" + re.sub(r"[^A-Za-z0-9]", "_", ident))[:40]


class Run:
    def __init__(self, text, b=False, i=False, color=None, size=None, highlight=None, field=None):
        self.text, self.b, self.i, self.color, self.size, self.highlight, self.field = text, b, i, color, size, highlight, field

    def xml(self):
        rpr = ""
        if self.b: rpr += "<w:b/>"
        if self.i: rpr += "<w:i/>"
        if self.color: rpr += f'<w:color w:val="{self.color}"/>'
        if self.size: rpr += f'<w:sz w:val="{int(self.size * 2)}"/><w:szCs w:val="{int(self.size * 2)}"/>'
        if self.highlight: rpr += f'<w:highlight w:val="{self.highlight}"/>'
        rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
        if self.field:
            return (f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{rpr}<w:instrText xml:space="preserve"> {_x(self.field)} </w:instrText></w:r>'
                    f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{rpr}<w:t xml:space="preserve">{_x(self.text)}</w:t></w:r>'
                    f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>')
        parts = re.split(r"(\t|\n)", self.text or "")
        inner = "".join("<w:tab/>" if p == "\t" else "<w:br/>" if p == "\n" else f'<w:t xml:space="preserve">{_x(p)}</w:t>' for p in parts if p != "")
        return f"<w:r>{rpr}{inner}</w:r>"


def runs_with_placeholders(text, size=None, b=False, color=None):
    """Placeholders such as [DECISION: …] are bold and highlighted so nobody misses them."""
    out, pos = [], 0
    for m in PH_RE.finditer(text or ""):
        if m.start() > pos:
            out.append(Run(text[pos:m.start()], b=b, size=size, color=color))
        out.append(Run(m.group(0), b=True, size=size, highlight="yellow"))
        pos = m.end()
    if pos < len(text or ""):
        out.append(Run(text[pos:], b=b, size=size, color=color))
    return out


class Doc:
    def __init__(self, lang="en"):
        self.lang, self.body, self._bm = lang, [], 0

    # ---- blocks
    def para(self, runs, style=None, indent=None, hanging=None, keep=False, align=None, marks=(), tab=None, space_after=None):
        if isinstance(runs, str):
            runs = [Run(runs)]
        ppr = ""
        if style: ppr += f'<w:pStyle w:val="{style}"/>'
        if keep: ppr += "<w:keepNext/>"
        if tab: ppr += f'<w:tabs><w:tab w:val="left" w:pos="{int(tab * CM)}"/></w:tabs>'
        if space_after is not None: ppr += f'<w:spacing w:after="{int(space_after * 20)}"/>'
        if indent is not None or hanging is not None:
            ppr += f'<w:ind w:left="{int((indent or 0) * CM)}"' + (f' w:hanging="{int(hanging * CM)}"' if hanging else "") + "/>"
        if align: ppr += f'<w:jc w:val="{align}"/>'
        starts, ends = "", ""
        for name in marks:
            self._bm += 1
            starts += f'<w:bookmarkStart w:id="{self._bm}" w:name="{_x(name)}"/>'
            ends += f'<w:bookmarkEnd w:id="{self._bm}"/>'
        self.body.append(f"<w:p>{'<w:pPr>' + ppr + '</w:pPr>' if ppr else ''}{starts}{''.join(r.xml() for r in runs)}{ends}</w:p>")

    def heading(self, text, level=1):
        self.para([Run(text)], style=f"Heading{level}")

    def title(self, text):
        self.para([Run(text)], style="Title")

    def bullet(self, text):
        self.para(runs_with_placeholders(text), style="ListBullet")

    def page_break(self):
        self.body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    def toc(self, hint):
        self.para([Run(hint, i=True, color=GREY, field='TOC \\o "1-1" \\h \\z \\u')])

    def table(self, cols, rows, widths_cm, font_pt=9, header_fill=ACCENT, shade_first=False):
        total = sum(widths_cm)
        grid = "".join(f'<w:gridCol w:w="{int(w * CM)}"/>' for w in widths_cm)
        border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="A6B4BF"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
        x = [f'<w:tbl><w:tblPr><w:tblW w:w="{int(total * CM)}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{border}</w:tblBorders>'
             f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']

        def cell(text, w, fill=None, bold=False, color=None):
            shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
            runs = [Run(str(text), b=True, size=font_pt, color=color)] if bold else runs_with_placeholders("" if text is None else str(text), size=font_pt)
            paras = "".join(f'<w:p><w:pPr><w:spacing w:after="0"/></w:pPr>{"".join(r.xml() for r in rr)}</w:p>'
                            for rr in ([runs] if bold else [runs_with_placeholders(line, size=font_pt) for line in (str(text or "").split("\n") or [""])]))
            return f'<w:tc><w:tcPr><w:tcW w:w="{int(w * CM)}" w:type="dxa"/>{shd}</w:tcPr>{paras}</w:tc>'
        if cols:
            x.append('<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' + "".join(cell(c, widths_cm[i], header_fill, True, "FFFFFF") for i, c in enumerate(cols)) + "</w:tr>")
        for row in rows:
            x.append("<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(
                cell(v, widths_cm[i], "E8EEF2" if shade_first and i == 0 else None, shade_first and i == 0) for i, v in enumerate(row)) + "</w:tr>")
        x.append("</w:tbl>")
        self.body.append("".join(x))
        self.para("", space_after=2)

    def kv(self, pairs, widths=(5.0, 11.5)):
        self.table(None, pairs, list(widths), font_pt=9, shade_first=True)

    def banner(self, text, fill="FBEAEA", color=RED):
        self.body.append(f'<w:tbl><w:tblPr><w:tblW w:w="{int(16.5 * CM)}" w:type="dxa"/><w:jc w:val="center"/></w:tblPr><w:tblGrid><w:gridCol w:w="{int(16.5 * CM)}"/></w:tblGrid>'
                         f'<w:tr><w:tc><w:tcPr><w:tcW w:w="{int(16.5 * CM)}" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="{fill}"/></w:tcPr>'
                         f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="60" w:after="60"/></w:pPr>{Run(text, b=True, size=13, color=color).xml()}</w:p></w:tc></w:tr></w:tbl>')
        self.para("")

    # ---- package
    def build(self, core: dict, header_left: str, header_right: str, footer_left: str, page_word="Page", of_word="of") -> bytes:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        lang = "fr-CA" if self.lang == "fr" else "en-CA"
        sect = (f'<w:sectPr><w:headerReference w:type="default" r:id="rIdH"/><w:footerReference w:type="default" r:id="rIdF"/>'
                f'<w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="{int(2.2 * CM)}" w:right="{int(2.3 * CM)}" w:bottom="{int(2.0 * CM)}" w:left="{int(2.3 * CM)}" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>')
        doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document xmlns:w="{W}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
               f'<w:body>{"".join(self.body)}{sect}</w:body></w:document>')
        tabs = f'<w:tabs><w:tab w:val="right" w:pos="{int(16.9 * CM)}"/></w:tabs>'
        header = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:hdr xmlns:w="{W}"><w:p><w:pPr>{tabs}</w:pPr>'
                  f'{Run(header_left, size=8.5, color=GREY).xml()}{Run(chr(9)).xml()}{Run(header_right, b=True, size=8.5, color=RED).xml()}</w:p></w:hdr>')
        footer = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:ftr xmlns:w="{W}"><w:p><w:pPr>{tabs}</w:pPr>'
                  f'{Run(footer_left + chr(9) + page_word + " ", size=8.5, color=GREY).xml()}{Run("1", size=8.5, color=GREY, field="PAGE").xml()}'
                  f'{Run(" " + of_word + " ", size=8.5, color=GREY).xml()}{Run("1", size=8.5, color=GREY, field="NUMPAGES").xml()}</w:p></w:ftr>')
        cp = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
              f'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
              f'<dc:title>{_x(core.get("title"))}</dc:title><dc:subject>{_x(core.get("subject"))}</dc:subject><dc:creator>{_x(core.get("author"))}</dc:creator>'
              f'<cp:keywords>{_x(core.get("keywords"))}</cp:keywords><dc:description>{_x(core.get("comments"))}</dc:description><dc:identifier>{_x(core.get("identifier"))}</dc:identifier>'
              f'<dc:language>{lang}</dc:language><cp:category>{_x(core.get("category"))}</cp:category><cp:version>{_x(core.get("version"))}</cp:version>'
              f'<cp:lastModifiedBy>{_x(core.get("author"))}</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')
        files = {
            "[Content_Types].xml": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                                    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                                    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                                    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                                    '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
                                    '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                                    '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
                                    '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                                    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                                    '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>'),
            "_rels/.rels": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'),
            "word/_rels/document.xml.rels": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                             '<Relationship Id="rIdS" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                                             '<Relationship Id="rIdT" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
                                             '<Relationship Id="rIdN" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
                                             '<Relationship Id="rIdH" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>'
                                             '<Relationship Id="rIdF" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>'),
            "word/document.xml": doc, "word/header1.xml": header, "word/footer1.xml": footer, "word/styles.xml": _styles(lang),
            "word/settings.xml": (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:settings xmlns:w="{W}"><w:zoom w:percent="100"/>'
                                  f'<w:updateFields w:val="true"/><w:defaultTabStop w:val="720"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>'),
            "word/numbering.xml": (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:numbering xmlns:w="{W}"><w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>'
                                   '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
                                   '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>'),
            "docProps/core.xml": cp,
            "docProps/app.xml": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
                                 f'<Application>{_x(core.get("author"))}</Application></Properties>'),
        }
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name in ("[Content_Types].xml", "_rels/.rels", "word/_rels/document.xml.rels", "word/document.xml", "word/styles.xml", "word/settings.xml",
                         "word/numbering.xml", "word/header1.xml", "word/footer1.xml", "docProps/core.xml", "docProps/app.xml"):
                z.writestr(name, files[name])
        return buf.getvalue()


def _styles(lang):
    font = '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>'

    def head(sid, name, size, color, before, lvl=None, ui=9):
        out = f'<w:outlineLvl w:val="{lvl}"/>' if lvl is not None else ""
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="{ui}"/><w:qFormat/>'
                f'<w:pPr><w:keepNext/><w:spacing w:before="{before * 20}" w:after="120"/>{out}</w:pPr><w:rPr>{font}<w:b/><w:color w:val="{color}"/><w:sz w:val="{size * 2}"/></w:rPr></w:style>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles xmlns:w="{W}">'
            f'<w:docDefaults><w:rPrDefault><w:rPr>{font}<w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="{lang}"/></w:rPr></w:rPrDefault>'
            '<w:pPrDefault><w:pPr><w:spacing w:after="100" w:line="269" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
            f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:rPr>{font}<w:color w:val="{INK}"/><w:sz w:val="21"/></w:rPr></w:style>'
            + head("Title", "Title", 22, INK, 0, None, 10) + head("Heading1", "heading 1", 14, ACCENT, 16, 0) + head("Heading2", "heading 2", 12, ACCENT, 10, 1)
            + f'<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr></w:style>'
            + '<w:style w:type="paragraph" w:styleId="TOC1"><w:name w:val="toc 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="39"/><w:pPr><w:spacing w:after="60"/></w:pPr></w:style>'
            + '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont"><w:name w:val="Default Paragraph Font"/><w:uiPriority w:val="1"/></w:style>'
            + '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'
            + "</w:styles>")


# ------------------------------------------------------------------ reader
MAX_UNZIPPED = 200 * 1024 * 1024


class NotAWordFile(Exception):
    pass


def read(data: bytes) -> dict:
    """Body paragraphs (outside tables) with text, style and bookmark names, plus the core properties."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise NotAWordFile("This is not a Word (.docx) file.") from e
    names = z.namelist()
    if "word/document.xml" not in names:
        raise NotAWordFile("This is not a Word (.docx) file.")
    if any(n.lower().endswith("vbaproject.bin") for n in names):
        raise NotAWordFile("Macro-enabled documents are refused.")
    if len(names) > 5000 or sum(i.file_size for i in z.infolist()) > MAX_UNZIPPED:
        raise NotAWordFile("The archive is too large to be a policy document.")
    import xml.etree.ElementTree as ET
    core = {}
    if "docProps/core.xml" in names:
        root = ET.fromstring(z.read("docProps/core.xml"))
        for el in root:
            core[el.tag.split("}")[1]] = (el.text or "").strip()
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find("w:body", NS)
    paras = []
    q = lambda t: f"{{{W}}}{t}"                                            # noqa: E731
    for el in body:
        if el.tag != q("p"):
            continue                                                       # tables are not read back
        style = el.find("w:pPr/w:pStyle", NS)
        sty = style.get(q("val")) if style is not None else ""
        marks = [b.get(q("name")) for b in el.iter(q("bookmarkStart"))]
        txt = []
        for node in el.iter():
            if node.tag == q("t"):
                txt.append(node.text or "")
            elif node.tag == q("tab"):
                txt.append("\t")
            elif node.tag in (q("br"), q("cr")) and node.get(q("type")) != "page":
                txt.append("\n")
        # text inside w:del is in w:delText and is not collected; w:ins text is kept (accepted reading)
        paras.append({"text": "".join(txt), "style": sty, "marks": [m for m in marks if m]})
    return {"core": core, "paragraphs": paras}
