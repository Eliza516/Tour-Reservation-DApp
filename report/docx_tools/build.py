import re, os, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image

ROOT = '/home/user/Tour-Reservation-DApp/report/overleaf'
OUT = '/home/user/Tour-Reservation-DApp/report/BaoCao_De36_TourReservationDApp.docx'
WORK = os.path.dirname(os.path.abspath(__file__))
FONT = 'Times New Roman'
MONO = 'Consolas'
NAVY = '0D2137'

# ---------------------------------------------------------------- inline parser
def read_group(s, i):
    """s[i]=='{' -> (content, index after closing)"""
    assert s[i] == '{', s[i:i+30]
    depth = 0; j = i
    while j < len(s):
        c = s[j]
        if c == '\\': j += 2; continue
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return s[i+1:j], j+1
        j += 1
    raise ValueError('unbalanced: ' + s[i:i+60])

SYM = {'times': '×', 'approx': '≈', 'ge': '≥', 'le': '≤', 'ne': '≠', 'rightarrow': '→',
       'leftrightarrow': '↔', 'Rightarrow': '⇒', 'dots': '…', 'quad': ' ', 'allowbreak': '',
       'newline': '\n', 'small': '', 'footnotesize': '', 'centering': '', 'hline': ''}
ESC = {'_': '_', '^': '^', '{': '{', '}': '}', '&': '&', '%': '%', '#': '#', '$': '$', ',': '\u202f',
       ';': ' ', ' ': ' ', '-': '', '\\': '\n'}

class Ctx:
    labels = {}      # label -> display string
    cites = {}

def parse_inline(s, st=None, math=False):
    st = dict(st or {})
    runs = []
    def emit(t, **kw):
        if t == '': return
        d = dict(st); d.update(kw); d['text'] = t; runs.append(d)
    i = 0; buf = ''
    def flush():
        nonlocal buf
        if buf: emit(buf); buf = ''
    while i < len(s):
        c = s[i]
        if c == '\\':
            m = re.match(r'\\([A-Za-z]+)', s[i:])
            if m:
                name = m.group(1); i += len(m.group(0))
                if name in ('textbf', 'emph', 'textit', 'code', 'texttt', 'todo', 'textcolor', 'ref', 'cite', 'mathrm', 'text'):
                    if name == 'textcolor':
                        _, i = read_group(s, i)
                    while i < len(s) and s[i] == ' ' and False: i += 1
                    arg, i = read_group(s, i)
                    flush()
                    if name == 'textbf': runs += parse_inline(arg, {**st, 'b': True}, math)
                    elif name in ('emph', 'textit'): runs += parse_inline(arg, {**st, 'i': True}, math)
                    elif name in ('code', 'texttt'): runs += parse_inline(arg, {**st, 'mono': True}, math)
                    elif name == 'todo': runs += parse_inline('[' + arg + ']', {**st, 'b': True, 'color': 'FF0000'}, math)
                    elif name in ('mathrm', 'text', 'textcolor'): runs += parse_inline(arg, st, math)
                    elif name == 'ref':
                        runs.append({**st, 'text': Ctx.labels.get(arg, '??' + arg)})
                    elif name == 'cite':
                        runs.append({**st, 'text': '[' + Ctx.cites.get(arg, '?') + ']'})
                    continue
                if name in ('vspace', 'hspace'):
                    _, i = read_group(s, i); continue
                if name in SYM:
                    buf += SYM[name]
                    if i < len(s) and s[i] == ' ': i += 1
                    continue
                # unknown command: drop
                if i < len(s) and s[i] == ' ': i += 1
                continue
            else:
                nxt = s[i+1] if i+1 < len(s) else ''
                if nxt == '^' and s[i+2:i+4] == '{}':
                    buf += '^'; i += 4; continue
                buf += ESC.get(nxt, nxt); i += 2; continue
        if c == '$':
            j = s.index('$', i+1)
            flush(); runs += parse_inline(s[i+1:j], st, True); i = j+1; continue
        if c == '^' and math:
            flush(); i += 1
            if i < len(s) and s[i] == '{':
                arg, i = read_group(s, i)
            else:
                arg = s[i]; i += 1
            runs += parse_inline(arg, {**st, 'sup': True}, True); continue
        if c == '{':
            arg, j = read_group(s, i)
            if arg == ',' : buf += ','
            else:
                flush(); runs += parse_inline(arg, st, math)
            i = j; continue
        if c == '}': i += 1; continue
        if c == '~': buf += '\u00a0'; i += 1; continue
        if s.startswith('---', i): buf += '—'; i += 3; continue
        if s.startswith('--', i): buf += '–'; i += 2; continue
        if not st.get('mono'):
            if s.startswith('``', i): buf += '“'; i += 2; continue
            if s.startswith("''", i): buf += '”'; i += 2; continue
        if math and c == '-' : buf += '−'; i += 1; continue
        if c in '\r': i += 1; continue
        if c == '\n': buf += ' '; i += 1; continue
        buf += c; i += 1
    flush()
    return runs

def plain(s):
    return ''.join(r['text'] for r in parse_inline(s))

# ---------------------------------------------------------------- docx helpers
def set_run_font(run, name=FONT, size=None):
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): rf.set(qn(a), name)
    if size: run.font.size = Pt(size)

def add_runs(p, runs, size=None, color=None, bold=None):
    for r in runs:
        parts = r['text'].split('\n')
        for k, t in enumerate(parts):
            if k > 0: p.add_run().add_break()
            if t == '': continue
            run = p.add_run(t)
            mono = r.get('mono')
            set_run_font(run, MONO if mono else FONT, (size - 1 if (mono and size) else size))
            if r.get('b') or bold: run.bold = True
            if r.get('i'): run.italic = True
            if r.get('sup'): run.font.superscript = True
            col = r.get('color') or color
            if col: run.font.color.rgb = RGBColor.from_string(col)

def shade(cell_or_p, fill):
    el = cell_or_p._tc if hasattr(cell_or_p, '_tc') else cell_or_p._p
    pr = el.get_or_add_tcPr() if hasattr(cell_or_p, '_tc') else el.get_or_add_pPr()
    sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), fill)
    pr.append(sh)

def set_borders(table, color='999999', sz=4):
    tbl = table._tbl; tblPr = tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for e in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        x = OxmlElement('w:' + e); x.set(qn('w:val'), 'single'); x.set(qn('w:sz'), str(sz)); x.set(qn('w:space'), '0'); x.set(qn('w:color'), color); b.append(x)
    tblPr.append(b)

def cell_margins(table, top=60, bottom=60, left=100, right=100):
    tblPr = table._tbl.tblPr
    m = OxmlElement('w:tblCellMar')
    for k, v in (('top', top), ('left', left), ('bottom', bottom), ('right', right)):
        x = OxmlElement('w:' + k); x.set(qn('w:w'), str(v)); x.set(qn('w:type'), 'dxa'); m.append(x)
    tblPr.append(m)

def fixed_layout(table, widths_dxa):
    tblPr = table._tbl.tblPr
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    tw = tblPr.find(qn('w:tblW'))
    if tw is None:
        tw = OxmlElement('w:tblW'); tblPr.append(tw)
    tw.set(qn('w:w'), str(sum(widths_dxa))); tw.set(qn('w:type'), 'dxa')
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn('w:gridCol')), widths_dxa): gc.set(qn('w:w'), str(w))
    for row in table.rows:
        for c, w in zip(row.cells, widths_dxa):
            c.width = Emu(w * 635)

def keep_next(p): p.paragraph_format.keep_with_next = True

def add_field(p, instr, cached=''):
    def fc(t):
        r = p.add_run(); f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), t); r._r.append(f); return r
    fc('begin')
    r = p.add_run(); it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = instr; r._r.append(it)
    fc('separate')
    rr = p.add_run(cached); set_run_font(rr, FONT, 11)
    fc('end')

# ---------------------------------------------------------------- tex block parser
BLOCK_START = re.compile(r'^\\(section|subsection|subsubsection|begin\{(itemize|enumerate|table|figure|lstlisting|infobox|warnbox|successbox)\}|shot\{|lstinputlisting|newpage|appendix|renewcommand|label\{|include)')

def find_end(s, i, env):
    j = s.index('\\end{%s}' % env, i)
    return j, j + len('\\end{%s}' % env)

def skip_opt(s, i):
    while i < len(s) and s[i] in ' \n': i += 1
    if i < len(s) and s[i] == '[':
        depth = 0
        while True:
            if s[i] == '[': depth += 1
            elif s[i] == ']':
                depth -= 1
                if depth == 0: return i + 1
            elif s[i] == '{':
                _, i = read_group(s, i); continue
            i += 1
    return i

def strip_comments(s):
    return re.sub(r'(?<!\\)%.*', '', s)

class Counters:
    sec = 0; sub = 0; subsub = 0; fig = 0; tab = 0; lst = 0; appendix = False

def parse_tex(src, blocks):
    C = Counters
    s = strip_comments(src)
    lines = s.split('\n')
    n = len(lines); k = 0
    pending_label_target = None
    while k < n:
        line = lines[k]
        st = line.strip()
        if not st: k += 1; continue
        m = BLOCK_START.match(st)
        if not m:
            # paragraph
            para = [st]; k += 1
            while k < n and lines[k].strip() and not BLOCK_START.match(lines[k].strip()):
                para.append(lines[k].strip()); k += 1
            txt = ' '.join(para)
            if txt.startswith('\\') and re.match(r'\\(vspace|hspace|thesection)', txt): continue
            blocks.append(('p', txt)); continue
        kind = m.group(1)
        if kind == 'appendix': C.appendix = True; C.sec = 0; k += 1; continue
        if kind in ('newpage', 'renewcommand', 'include'): k += 1; continue
        if kind.startswith('label'):
            lab = re.match(r'\\label\{([^}]*)\}', st).group(1)
            Ctx.labels[lab] = pending_label_target or '?'
            k += 1; continue
        if kind in ('section', 'subsection', 'subsubsection'):
            # heading may be followed on same line by \label
            rest = '\n'.join(lines[k:])
            i = rest.index('{')
            title, j = read_group(rest, i)
            if kind == 'section':
                C.sec += 1; C.sub = 0; C.subsub = 0
                num = ('Phụ lục ' + chr(64 + C.sec)) if C.appendix else ('Chương %d' % C.sec)
                label_text = num
                blocks.append(('h1', num, title))
            elif kind == 'subsection':
                C.sub += 1; C.subsub = 0
                num = '%d.%d' % (C.sec, C.sub) if not C.appendix else '%s.%d' % (chr(64 + C.sec), C.sub)
                label_text = num; blocks.append(('h2', num, title))
            else:
                C.subsub += 1
                num = '%d.%d.%d' % (C.sec, C.sub, C.subsub); label_text = num
                blocks.append(('h3', num, title))
            pending_label_target = label_text
            consumed = rest[:j].count('\n')
            k += consumed + 1
            # label on remainder of this line
            tail = rest[j:].split('\n')[0]
            mm = re.search(r'\\label\{([^}]*)\}', tail)
            if mm: Ctx.labels[mm.group(1)] = label_text
            continue
        # environments: collect text from k
        rest = '\n'.join(lines[k:])
        if kind == 'shot{':
            i = rest.index('{')
            f, i = read_group(rest, rest.index('\\shot') + 5)
            cap, i = read_group(rest, i)
            w, i = read_group(rest, i)
            C.fig += 1
            Ctx.labels['fig:' + f] = str(C.fig)
            blocks.append(('fig', f, cap, float(w), C.fig))
            k += rest[:i].count('\n') + 1; continue
        if kind == 'lstinputlisting':
            i = rest.index('\\lstinputlisting') + len('\\lstinputlisting')
            e = skip_opt(rest, i); opts = rest[i:e]
            fpath, e2 = read_group(rest, e)
            fl = re.search(r'firstline=(\d+)', opts); ll = re.search(r'lastline=(\d+)', opts)
            cm = re.search(r'caption=', opts); cap = ''
            if cm: cap, _ = read_group(opts, cm.end())
            C.lst += 1
            blocks.append(('code_file', fpath, int(fl.group(1)) if fl else 1, int(ll.group(1)) if ll else None, cap, C.lst))
            k += rest[:e2].count('\n') + 1; continue
        env = m.group(2)
        # \begin{env}
        bi = rest.index('\\begin{%s}' % env) + len('\\begin{%s}' % env)
        j, e = find_end(rest, bi, env)
        body = rest[bi:j]
        consumed = rest[:e].count('\n') + 1
        if env in ('itemize', 'enumerate'):
            body = body[skip_opt(body, 0):] if body.lstrip().startswith('[') else body
            items = re.split(r'\\item', body)[1:]
            out = []
            for it in items:
                lab = None
                mm = re.match(r'\s*\[([^\]]*)\]', it)
                if mm: lab = mm.group(1); it = it[mm.end():]
                out.append((lab, ' '.join(x.strip() for x in it.strip().split('\n'))))
            blocks.append(('list', env, out))
        elif env in ('infobox', 'warnbox', 'successbox'):
            blocks.append(('box', env, ' '.join(x.strip() for x in body.strip().split('\n'))))
        elif env == 'lstlisting':
            ob = skip_opt(body, 0); opts = body[:ob]; code = body[ob:].strip('\n')
            cm = re.search(r'caption=', opts); cap = ''
            if cm: cap, _ = read_group(opts, cm.end())
            C.lst += 1
            blocks.append(('code_raw', code, cap, C.lst))
        elif env == 'figure':
            cm = body.index('\\caption'); cap, _ = read_group(body, cm + 8)
            lab = re.search(r'\\label\{([^}]*)\}', body).group(1)
            C.fig += 1; Ctx.labels[lab] = str(C.fig)
            blocks.append(('fig', 'arch.png', cap, 0.95, C.fig))
        elif env == 'table':
            cm = body.index('\\caption'); cap, ce = read_group(body, cm + 8)
            lm = re.search(r'\\label\{([^}]*)\}', body)
            C.tab += 1
            if lm: Ctx.labels[lm.group(1)] = str(C.tab)
            tb = body.index('\\begin{tabularx}')
            spec_start = body.index('}', tb + 16) + 1  # after {\linewidth}
            spec, se = read_group(body, spec_start)
            te = body.index('\\end{tabularx}')
            tbody = body[se:te]
            blocks.append(('table', cap, spec, tbody, C.tab))
        k += consumed
    return blocks

# ---------------------------------------------------------------- build document
def main():
    # bib
    bib = open(os.path.join(ROOT, 'main.bib'), encoding='utf8').read()
    entries = re.findall(r'@\w+\{(\w+),(.*?)\n\}', bib, re.S)
    keys = [e[0] for e in entries]
    order = ['eip1193'] + [k for k in keys if k != 'eip1193']
    for n, k in enumerate(order, 1): Ctx.cites[k] = str(n)

    blocks = []
    files = ['2-Chapter1', '3-Chapter2', '4-Chapter3', '5-Chapter4', '6-Chapter5', '7-Chapter6', '8-Chapter7', '9-Chapter8', '10-Appendix']
    for f in files:
        parse_tex(open(os.path.join(ROOT, 'Sections', f + '.tex'), encoding='utf8').read(), blocks)

    # architecture picture (cropped)
    im = Image.open(os.path.join(WORK, 'arch.png')); im.crop((40, 100, 1660, 730)).save(os.path.join(WORK, 'arch_c.png'))

    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21); sec.page_height = Cm(29.7)
    sec.left_margin = Cm(3); sec.right_margin = Cm(2); sec.top_margin = Cm(2.5); sec.bottom_margin = Cm(2.2)
    TEXTW = 16.0  # cm

    # styles
    stn = doc.styles['Normal']; stn.font.name = FONT; stn.font.size = Pt(13)
    stn.element.rPr.rFonts.set(qn('w:eastAsia'), FONT); stn.element.rPr.rFonts.set(qn('w:cs'), FONT)
    stn.paragraph_format.space_after = Pt(6); stn.paragraph_format.line_spacing = 1.3
    for name, size, before, after, col in (('Heading 1', 18, 18, 10, NAVY), ('Heading 2', 15, 14, 6, '1565C0'), ('Heading 3', 13.5, 10, 4, '37474F')):
        h = doc.styles[name]; h.font.name = FONT; h.font.size = Pt(size); h.font.bold = True
        h.font.color.rgb = RGBColor.from_string(col)
        rf = h.element.rPr.rFonts
        for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): rf.set(qn(a), FONT)
        for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
            if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
        h.paragraph_format.space_before = Pt(before); h.paragraph_format.space_after = Pt(after)
        h.paragraph_format.keep_with_next = True; h.paragraph_format.line_spacing = 1.15
    cap = doc.styles['Caption']; cap.font.name = FONT; cap.font.size = Pt(11.5); cap.font.italic = False; cap.font.bold = False
    cap.font.color.rgb = RGBColor(0x37, 0x47, 0x4F); cap.paragraph_format.space_after = Pt(10)

    # header / footer
    hp = sec.header.paragraphs[0]; hp.text = ''
    r = hp.add_run('Khoa Khoa học Dữ liệu và Trí tuệ nhân tạo'); set_run_font(r, FONT, 10); r.bold = True
    pb = OxmlElement('w:pBdr'); bt = OxmlElement('w:bottom'); bt.set(qn('w:val'), 'single'); bt.set(qn('w:sz'), '4'); bt.set(qn('w:space'), '1'); bt.set(qn('w:color'), '808080'); pb.append(bt); hp._p.get_or_add_pPr().append(pb)
    fp = sec.footer.paragraphs[0]; fp.text = ''
    r = fp.add_run('Báo cáo Đề 36 — Tour Reservation DApp\t\tTrang '); set_run_font(r, FONT, 10)
    add_field(fp, 'PAGE', '1'); r = fp.add_run(' / '); set_run_font(r, FONT, 10); add_field(fp, 'NUMPAGES', '1')
    fp.paragraph_format.tab_stops.add_tab_stop(Cm(TEXTW), alignment=2)
    for rr in fp.runs: set_run_font(rr, FONT, 10)

    sec.different_first_page_header_footer = True

    # ---- cover
    def center(text, size, bold=False, color=None, after=6, before=0):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(before)
        runs = parse_inline(text)
        add_runs(p, runs, size=size, color=color, bold=bold); return p
    center('TRƯỜNG ĐẠI HỌC KINH TẾ QUỐC DÂN', 14, True, after=0)
    center('VIỆN CÔNG NGHỆ', 14, True, after=0)
    center('KHOA KHOA HỌC DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO', 14, True, after=14)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(ROOT, 'Images', 'NEU logo.png'), width=Cm(3.6))
    center('\\todo{TÊN HỌC PHẦN}', 18, True, after=10, before=14)
    center('BÁO CÁO BÀI TẬP LỚN', 16, True, color=NAVY, after=10)
    center('Đề 36: Tour Reservation DApp', 28, True, color=NAVY, after=8)
    center('Ứng dụng phi tập trung đặt chỗ tour du lịch trên Ethereum (Sepolia)', 14, True, after=26)
    info = [('Học phần:', '\\todo{Tên học phần / mã học phần}'), ('Giảng viên:', '\\todo{Họ tên giảng viên hướng dẫn}'),
            ('Sinh viên:', '\\todo{Họ và tên}   \\textbf{\\todo{MSSV}}'), ('Lớp:', '\\todo{Lớp / nhóm}'),
            ('Smart Contract:', 'Solidity \\code{\\^{}0.8.20} (biên dịch bằng 0.8.34)'),
            ('Giao diện:', 'React + Vite + web3.js'), ('Mạng triển khai:', 'Ethereum Sepolia Testnet')]
    t = doc.add_table(rows=len(info), cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row, (a, b) in zip(t.rows, info):
        pa = row.cells[0].paragraphs[0]; add_runs(pa, [{'text': a, 'b': True}], size=13); pa.paragraph_format.space_after = Pt(3)
        pb_ = row.cells[1].paragraphs[0]; add_runs(pb_, parse_inline(b), size=13); pb_.paragraph_format.space_after = Pt(3)
    fixed_layout(t, [2600, 5600])
    center('Hà Nội, tháng 11 năm 2026', 12, after=0, before=40)
    doc.add_page_break()

    # ---- TOC (field with cached entries)
    p = doc.add_paragraph(); r = p.add_run('MỤC LỤC'); set_run_font(r, FONT, 16); r.bold = True; r.font.color.rgb = RGBColor.from_string(NAVY)
    toc_entries = [(b[0], b[1], b[2]) for b in blocks if b[0] in ('h1', 'h2', 'h3')]
    first = True
    for idx, (kind, num, title) in enumerate(toc_entries):
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2); p.paragraph_format.line_spacing = 1.1
        p.paragraph_format.left_indent = Cm({'h1': 0, 'h2': 0.7, 'h3': 1.4}[kind])
        if first:
            def fc(t_):
                rr = p.add_run(); f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), t_); rr._r.append(f)
            fc('begin'); rr = p.add_run(); it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = ' TOC \\o "1-3" \\h \\z \\u '; rr._r.append(it); fc('separate'); first = False
        label = (num + '. ' if kind == 'h1' else num + ' ') + plain(title)
        rr = p.add_run(label); set_run_font(rr, FONT, 12); rr.bold = (kind == 'h1')
        if idx == len(toc_entries) - 1:
            f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), 'end'); p.add_run()._r.append(f)
    p = doc.add_paragraph(); r = p.add_run('(Nhấn chuột phải vào mục lục → Update Field → Update entire table để cập nhật số trang.)'); set_run_font(r, FONT, 10); r.italic = True
    doc.add_page_break()

    # ---- body
    def para(runs, style=None, align=None, indent=None, after=None, size=None):
        p = doc.add_paragraph(style=style)
        if align == 'j': p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_runs(p, runs, size=size)
        if after is not None: p.paragraph_format.space_after = Pt(after)
        return p

    def code_box(lines, size=9):
        t = doc.add_table(rows=1, cols=1); set_borders(t, 'B0B7BD', 4); cell_margins(t, 80, 80, 140, 140)
        c = t.rows[0].cells[0]; shade(c, 'F8F9FA')
        first = True
        for ln in lines:
            p = c.paragraphs[0] if first else c.add_paragraph(); first = False
            p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            r = p.add_run(ln.replace('\t', '  ') if ln else ' '); set_run_font(r, MONO, size)
        fixed_layout(t, [int(TEXTW / 2.54 * 1440)])
        return t

    def caption_p(text_runs, label, num, above=False):
        p = doc.add_paragraph(style='Caption'); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, [{'text': '%s %d: ' % (label, num), 'b': True}] + text_runs, size=11.5)
        if not above: p.paragraph_format.space_before = Pt(4)
        if above: p.paragraph_format.keep_with_next = True; p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(4)
        return p

    first_h1 = True
    for b in blocks:
        k = b[0]
        if k == 'h1':
            if not first_h1: doc.add_page_break()
            first_h1 = False
            p = doc.add_heading(level=1)
            add_runs(p, [{'text': b[1] + '. '}] + parse_inline(b[2]), size=18)
        elif k in ('h2', 'h3'):
            p = doc.add_heading(level=2 if k == 'h2' else 3)
            add_runs(p, [{'text': b[1] + ' '}] + parse_inline(b[2]), size=15 if k == 'h2' else 13.5)
        elif k == 'p':
            para(parse_inline(b[1]), align='j')
        elif k == 'list':
            env, items = b[1], b[2]
            for n, (lab, txt) in enumerate(items, 1):
                p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(1.2); p.paragraph_format.first_line_indent = Cm(-0.7)
                p.paragraph_format.space_after = Pt(3)
                marker = lab if lab else ('•' if env == 'itemize' else '%d.' % n)
                p.paragraph_format.tab_stops.add_tab_stop(Cm(1.2))
                add_runs(p, [{'text': marker + '\t'}] + parse_inline(txt))
            doc.paragraphs[-1].paragraph_format.space_after = Pt(8)
        elif k == 'fig':
            f, capt, w, num = b[1], b[2], b[3], b[4]
            path = os.path.join(WORK, 'arch_c.png') if f == 'arch.png' else os.path.join(ROOT, 'Images', f)
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
            p.paragraph_format.space_after = Pt(2)
            p.add_run().add_picture(path, width=Cm(min(w, 0.98) * TEXTW))
            caption_p(parse_inline(capt), 'Hình', num)
        elif k == 'table':
            capt, spec, tbody, num = b[1], b[2], b[3], b[4]
            caption_p(parse_inline(capt), 'Bảng', num, above=True)
            cols = re.findall(r'[lcrX]', re.sub(r'\{[^}]*\}', '', spec))
            rows_raw = [r_ for r_ in re.split(r'\\\\(?![A-Za-z])', tbody) if r_.strip() and r_.strip() != '\\hline']
            rows = []
            for rr in rows_raw:
                color = None
                m = re.search(r'\\rowcolor\{(\w+)\}', rr)
                if m: color = m.group(1)
                rr = re.sub(r'\\rowcolor\{\w+\}', '', rr); rr = rr.replace('\\hline', '').strip()
                if not rr: continue
                cells = re.split(r'(?<!\\)&', rr)
                rows.append((color, [c.strip() for c in cells]))
            nc = len(cols)
            t = doc.add_table(rows=len(rows), cols=nc); set_borders(t, 'A0A7AD', 4); cell_margins(t, 50, 50, 90, 90)
            # widths
            wts = []
            for ci in range(nc):
                lens = [len(plain(r_[1][ci])) for r_ in rows if ci < len(r_[1])]
                avg = sum(lens) / max(len(lens), 1)
                mx = max(lens) if lens else 5
                w = min(max(avg * 0.6 + mx * 0.4, 5), 48)
                tok = max([len(x) for r_ in rows if ci < len(r_[1]) for x in plain(r_[1][ci]).split() ] or [3]) if True else 3
                w = max(w, min(tok * 1.3 + 2, 36))
                if cols[ci] == 'X': w = max(w, 22)
                wts.append(w)
            tot = TEXTW / 2.54 * 1440
            widths = [int(tot * w / sum(wts)) for w in wts]; widths[-1] += int(tot) - sum(widths)
            for ri, (color, cells) in enumerate(rows):
                hdr = (color == 'navyblue')
                for ci in range(nc):
                    cell = t.rows[ri].cells[ci]
                    txt = cells[ci] if ci < len(cells) else ''
                    p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.1
                    if cols[ci] == 'c': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    add_runs(p, parse_inline(txt), size=11, color='FFFFFF' if hdr else None, bold=True if hdr else None)
                    if hdr: shade(cell, NAVY)
                    elif color == 'rowgray': shade(cell, 'F5F8FC')
            # repeat header row
            trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement('w:tblHeader'); trPr.append(th)
            for row in t.rows:
                trPr = row._tr.get_or_add_trPr(); cs = OxmlElement('w:cantSplit'); trPr.append(cs)
            fixed_layout(t, widths)
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
        elif k == 'box':
            env, txt = b[1], b[2]
            fill = {'infobox': 'E3F2FD', 'successbox': 'E8F5E9', 'warnbox': 'FFEBEE'}[env]
            line = {'infobox': '1565C0', 'successbox': '2E7D32', 'warnbox': 'B71C1C'}[env]
            t = doc.add_table(rows=1, cols=1); set_borders(t, line, 8); cell_margins(t, 100, 100, 160, 160)
            c = t.rows[0].cells[0]; shade(c, fill)
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_runs(p, parse_inline(txt), size=12)
            fixed_layout(t, [int(TEXTW / 2.54 * 1440)])
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
        elif k == 'code_file':
            fpath, fl, ll, capt, num = b[1:]
            lines = open(os.path.join(ROOT, fpath), encoding='utf8').read().split('\n')
            seg = lines[fl - 1:(ll if ll else len(lines))]
            while seg and seg[-1] == '': seg.pop()
            code_box(seg, 9)
            caption_p(parse_inline(capt), 'Đoạn mã', num)
        elif k == 'code_raw':
            code, capt, num = b[1:]
            code_box(code.split('\n'), 9)
            caption_p(parse_inline(capt), 'Đoạn mã', num)

    # ---- bibliography
    doc.add_page_break()
    p = doc.add_heading(level=1); add_runs(p, [{'text': 'Tài liệu tham khảo'}], size=18)
    for n, k in enumerate(order, 1):
        body = dict(entries)[k]
        g = lambda f: (re.search(f + r'\s*=\s*\{(.*)\},?\s*$', body, re.M) or [None, ''])[1] if re.search(f + r'\s*=', body) else ''
        title = g('title'); auth = g('author'); url = g('url'); year = g('year'); note = g('note')
        title = title.replace('---', '—').replace('{', '').replace('}', ''); auth = auth.replace('{', '').replace('}', '')
        p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.first_line_indent = Cm(-1.0)
        txt = '[%d]\t%s%s. %s. %s %s' % (n, (auth + '. ') if auth else '', title, year, url, ('(' + note + ')') if note else '')
        p.paragraph_format.tab_stops.add_tab_stop(Cm(1.0))
        add_runs(p, [{'text': txt}], size=12)

    # update fields on open
    st = doc.settings.element
    uf = OxmlElement('w:updateFields'); uf.set(qn('w:val'), 'true'); st.append(uf)
    doc.core_properties.title = 'Báo cáo Đề 36 - Tour Reservation DApp'
    doc.save(OUT)
    print('saved', OUT)

main()
