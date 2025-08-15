import fitz, docx
def read_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for p in doc: text += p.get_text()
    return text
def read_docx(file):
    d = docx.Document(file); parts=[]
    for p in d.paragraphs: parts.append(p.text)
    for t in d.tables:
        for r in t.rows:
            for c in r.cells: parts.append(c.text)
    try:
        sec=d.sections[0]
        for p in sec.footer.paragraphs: parts.append(p.text)
    except Exception: pass
    return "\n".join(parts)
def read_any(file):
    if file.type=="application/pdf": return read_pdf(file)
    if file.type=="application/vnd.openxmlformats-officedocument.wordprocessingml.document": return read_docx(file)
    return file.read().decode("utf-8", errors="ignore")
