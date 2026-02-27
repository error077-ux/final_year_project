import textwrap

PAGE_W = 595
PAGE_H = 842
MARGIN = 50
LINE_H = 14
FONT_SIZE = 11

class PDFBuilder:
    def __init__(self):
        self.objects = []

    def add_object(self, data: bytes) -> int:
        self.objects.append(data)
        return len(self.objects)

    def escape(self, s: str) -> str:
        return s.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')

    def build(self, pages_streams):
        font_obj = self.add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

        page_obj_nums = []
        content_obj_nums = []

        for stream in pages_streams:
            data = stream.encode('latin-1')
            content = f"<< /Length {len(data)} >>\nstream\n".encode('latin-1') + data + b"\nendstream"
            cnum = self.add_object(content)
            content_obj_nums.append(cnum)

        pages_kids_placeholder = []
        pages_obj_num = self.add_object(b"")

        for cnum in content_obj_nums:
            page = (
                f"<< /Type /Page /Parent {pages_obj_num} 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                f"/Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {cnum} 0 R >>"
            ).encode('latin-1')
            pnum = self.add_object(page)
            page_obj_nums.append(pnum)

        kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
        pages_obj = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>".encode('latin-1')
        self.objects[pages_obj_num - 1] = pages_obj

        catalog_obj = self.add_object(f"<< /Type /Catalog /Pages {pages_obj_num} 0 R >>".encode('latin-1'))

        out = bytearray(b"%PDF-1.4\n")
        xref = [0]
        for i, obj in enumerate(self.objects, start=1):
            xref.append(len(out))
            out.extend(f"{i} 0 obj\n".encode('latin-1'))
            out.extend(obj)
            out.extend(b"\nendobj\n")

        xref_pos = len(out)
        out.extend(f"xref\n0 {len(self.objects)+1}\n".encode('latin-1'))
        out.extend(b"0000000000 65535 f \n")
        for pos in xref[1:]:
            out.extend(f"{pos:010d} 00000 n \n".encode('latin-1'))

        out.extend(
            f"trailer\n<< /Size {len(self.objects)+1} /Root {catalog_obj} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode('latin-1')
        )
        return bytes(out)


def text_block(lines, y_start, title=False):
    cmds = ["BT", f"/F1 {14 if title else FONT_SIZE} Tf", f"1 0 0 1 {MARGIN} {y_start} Tm"]
    first = True
    for line in lines:
        if not first:
            cmds.append(f"0 -{LINE_H} Td")
        first = False
        cmds.append(f"({escape(line)}) Tj")
    cmds.append("ET")
    return "\n".join(cmds)


def escape(s):
    return s.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


def wrap_para(text, width=90):
    return textwrap.wrap(text, width=width)


def diagram_architecture(x=60, y=420):
    # Draw boxes and arrows
    c = []
    c.append("0.2 w")
    def box(x,y,w,h,label):
        c.append(f"{x} {y} {w} {h} re S")
        c.append("BT /F1 9 Tf")
        c.append(f"1 0 0 1 {x+5} {y+h/2-3} Tm ({escape(label)}) Tj ET")
    box(x, y+180, 120, 35, "Operator (Telegram)")
    box(x+180, y+180, 140, 35, "Telegram Bot API")
    box(x+360, y+180, 130, 35, "Endpoint Agent")
    # arrows
    c.append(f"{x+120} {y+198} m {x+180} {y+198} l S")
    c.append(f"{x+320} {y+192} m {x+360} {y+192} l S")
    c.append(f"{x+360} {y+204} m {x+320} {y+204} l S")
    # module boxes
    mods = ["Keylogger", "Clipboard", "SysInfo", "Screen/Webcam", "Shell", "Wi-Fi", "File Retrieval"]
    my = y+130
    for i,m in enumerate(mods):
        by = my - i*20
        box(x+360, by, 120, 16, m)
        c.append(f"{x+425} {y+180} m {x+420} {by+16} l S")
    return "\n".join(c)


def diagram_sequence(x=60, y=340):
    c=["0.3 w"]
    lanes=[x,x+130,x+260,x+390]
    labels=["Operator","Telegram API","Agent","Handler"]
    for lx,lb in zip(lanes,labels):
        c.append(f"{lx} {y+220} m {lx} {y} l S")
        c.append("BT /F1 9 Tf")
        c.append(f"1 0 0 1 {lx-20} {y+230} Tm ({lb}) Tj ET")
    def arrow(x1,y1,x2,y2,text):
        c.append(f"{x1} {y1} m {x2} {y2} l S")
        c.append("BT /F1 8 Tf")
        c.append(f"1 0 0 1 {(x1+x2)/2-20} {y1+4} Tm ({escape(text)}) Tj ET")
    yy=y+200
    arrow(lanes[0],yy,lanes[1],yy,"/cmd DEVICE ipconfig")
    yy-=30; arrow(lanes[1],yy,lanes[2],yy,"update payload")
    yy-=30; arrow(lanes[2],yy,lanes[2],yy-1,"validate target")
    yy-=30; arrow(lanes[2],yy,lanes[3],yy,"execute command")
    yy-=30; arrow(lanes[3],yy,lanes[2],yy,"stdout/stderr")
    yy-=30; arrow(lanes[2],yy,lanes[1],yy,"send response")
    yy-=30; arrow(lanes[1],yy,lanes[0],yy,"deliver output")
    return "\n".join(c)


def diagram_risk(x=80,y=360):
    c=["0.3 w"]
    steps=["Initial Access","Deployment","Persistence","Collection","Execution","Exfiltration"]
    bx=x
    by=y+160
    for i,s in enumerate(steps):
        c.append(f"{bx+i*80} {by} 70 24 re S")
        c.append("BT /F1 8 Tf")
        c.append(f"1 0 0 1 {bx+i*80+4} {by+8} Tm ({s}) Tj ET")
        if i< len(steps)-1:
            c.append(f"{bx+i*80+70} {by+12} m {bx+(i+1)*80} {by+12} l S")
    c.append(f"{x+140} {by-60} 220 28 re S")
    c.append("BT /F1 9 Tf")
    c.append(f"1 0 0 1 {x+150} {by-43} Tm (Defensive Controls: EDR, App Control, Egress Policy) Tj ET")
    for i in range(len(steps)):
        c.append(f"{x+250} {by-32} m {bx+i*80+35} {by} l S")
    return "\n".join(c)


def make_pages():
    pages=[]
    y=780
    p1=[]
    title=["TELEGRAM-BASED ENDPOINT MONITORING AND REMOTE ADMINISTRATION FRAMEWORK"]
    p1.append(text_block(title, y, title=True))
    y-=40
    meta=["Institutional Research Paper Format", "Student: [Your Name]   Register No.: [Your Number]", "Department: [Dept]   Institution: [Institution]", "Guide: [Guide Name]   Academic Year: [YYYY-YYYY]"]
    p1.append(text_block(meta,y))
    y-=90
    abs_t=["Abstract"]
    p1.append(text_block(abs_t,y,title=True)); y-=24
    abs_p=("This paper presents a Telegram-based endpoint monitoring framework designed for controlled cybersecurity research. "
           "The system supports telemetry collection, remote command execution, multi-device routing, and defensive analysis. "
           "Key modules include keystroke and clipboard capture, system profiling, screenshot/webcam acquisition, shell control, "
           "Wi-Fi profile enumeration, and file retrieval. Evaluation in a lab environment indicates responsive text-based command handling "
           "and predictable media-transfer delay. The project is documented with strict ethical guidance and blue-team mitigation recommendations.")
    p1.append(text_block(wrap_para(abs_p),y)); y-=170
    p1.append(text_block(["1. Introduction"],y,title=True)); y-=24
    intro=("Trusted messaging APIs can be abused as command channels because traffic appears legitimate. This work builds a realistic "
           "final-year prototype to study both offensive workflows and defensive detection points. Objectives include modular design, "
           "multi-endpoint control, performance evaluation, and institutional compliance.")
    p1.append(text_block(wrap_para(intro),y)); y-=90
    p1.append(text_block(["2. Literature Context"],y,title=True)); y-=24
    lit=("Prior studies and ATT&CK mappings show recurring phases: deployment, persistence, collection, execution, and exfiltration. "
         "Telegram APIs reduce setup complexity and support command plus file response channels, making them suitable for lab-scale emulation.")
    p1.append(text_block(wrap_para(lit),y))
    pages.append("\n".join(p1))

    p2=[]
    y=780
    p2.append(text_block(["3. Proposed System Architecture"],y,title=True)); y-=24
    arch=("The framework follows an Operator -> Telegram API -> Endpoint Agent model. The agent contains modular collectors and handlers. "
          "Figure 1 provides the architecture diagram in renderable diagram format.")
    p2.append(text_block(wrap_para(arch),y));
    p2.append(diagram_architecture())
    p2.append(text_block(["Figure 1: High-level architecture and module mapping."],120))
    pages.append("\n".join(p2))

    p3=[]; y=780
    p3.append(text_block(["4. Implementation and Command Workflow"],y,title=True)); y-=24
    impl=("Implementation uses Python modules for runtime control, command parsing, collection tasks, and response upload. "
          "Device IDs allow one operator chat to manage multiple endpoints safely in a lab.")
    p3.append(text_block(wrap_para(impl),y));
    p3.append(diagram_sequence())
    p3.append(text_block(["Figure 2: Command-processing sequence."],90))
    pages.append("\n".join(p3))

    p4=[]; y=780
    p4.append(text_block(["5. Evaluation"],y,title=True)); y-=24
    ev=("Evaluation criteria: command latency, success rate, media transfer practicality, and host resource footprint. "
        "Text commands generally return quickly; media commands take longer due to capture and upload overhead. "
        "Observed limits include network outages, webcam permission failures, and payload size constraints.")
    p4.append(text_block(wrap_para(ev),y)); y-=110
    p4.append(text_block(["6. Security Analysis and Defensive Insights"],y,title=True)); y-=24
    sec=("The prototype maps to common ATT&CK behaviors and is valuable for defender training. Recommended controls include startup-change alerts, "
         "behavioral EDR rules, process lineage monitoring, and egress policy restrictions for unauthorized Telegram traffic.")
    p4.append(text_block(wrap_para(sec),y));
    p4.append(diagram_risk())
    p4.append(text_block(["Figure 3: Risk lifecycle with defensive interception points."],110))
    pages.append("\n".join(p4))

    p5=[]; y=780
    p5.append(text_block(["7. Ethical and Institutional Compliance"],y,title=True)); y-=24
    eth=("This research must be executed only in authorized environments with written consent, faculty supervision, and non-sensitive data. "
         "All artifacts should be securely archived or deleted after assessment.")
    p5.append(text_block(wrap_para(eth),y)); y-=90
    p5.append(text_block(["8. Conclusion and Future Work"],y,title=True)); y-=24
    conc=("The project demonstrates a complete, multi-module endpoint monitoring framework suitable for cybersecurity education and adversary emulation. "
          "Future work: stronger key management, cross-platform agent support, safer opt-in execution, and automated blue-team analytics dashboards.")
    p5.append(text_block(wrap_para(conc),y)); y-=100
    p5.append(text_block(["References"],y,title=True)); y-=24
    refs=["[1] MITRE ATT&CK Enterprise Matrix.","[2] Telegram Bot API Documentation.","[3] NIST SP 800-53.","[4] Microsoft Windows Security Baselines.","[5] OWASP Logging Cheat Sheet."]
    p5.append(text_block(refs,y))
    pages.append("\n".join(p5))

    return pages

pdf = PDFBuilder().build(make_pages())
with open('RESEARCH_PAPER.pdf','wb') as f:
    f.write(pdf)
print('Generated RESEARCH_PAPER.pdf', len(pdf), 'bytes')
