import sys, zipfile, re
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def text_of_para(p):
    parts = []
    for node in p.iter():
        tag = node.tag
        if tag == W+'t':
            parts.append(node.text or '')
        elif tag == W+'tab':
            parts.append('\t')
        elif tag == W+'br':
            parts.append(' / ')
    return ''.join(parts)

def walk(elem, out, depth=0):
    for child in elem:
        tag = child.tag
        if tag == W+'p':
            t = text_of_para(child).strip()
            if t:
                out.append(t)
        elif tag == W+'tbl':
            for tr in child.findall(W+'tr'):
                cells = [text_of_para_all(tc) for tc in tr.findall(W+'tc')]
                out.append('   |   '.join(c for c in cells))
        # recurse into sdt / other containers
        elif tag in (W+'sdt', W+'sdtContent', W+'body'):
            walk(child, out, depth)

def text_of_para_all(tc):
    paras = [text_of_para(p).strip() for p in tc.findall('.//'+W+'p')]
    return ' '.join(x for x in paras if x)

def extract(path):
    z = zipfile.ZipFile(path)
    out = []
    for part in ['word/header1.xml','word/document.xml','word/footer1.xml']:
        try:
            xml = z.read(part).decode('utf-8')
        except KeyError:
            continue
        root = ET.fromstring(xml)
        body = root.find(W+'body') if root.find(W+'body') is not None else root
        marker = out.append(f'\n----- {part} -----')
        walk(body, out)
    return '\n'.join(out)

if __name__ == '__main__':
    print(extract(sys.argv[1]))
