from typing import List, Dict, Tuple
from docx import Document
from docx.shared import Pt, Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import textwrap
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from docx.table import _Cell

from lxml import etree
import re
from latex2mathml.converter import convert
import mathml2omml

from database.models.exam_question import ExamQuestion

font_name = "Times New Roman"
font_size = 9


def get_passage_text(exam_question: ExamQuestion):
    if exam_question.subject != "영어":
        return ""

    question_type_normal = ["글의 목적", "글의 분위기 / 심경", "대의 파악", "함의 추론", "도표 이해",
                            "내용 일치 / 불일치", "실용문 일치 / 불일치", "어법성 판단",
                            "단어 쓰임 판단", "빈칸 추론", "무관한 문장", "주어진 문장 넣기"]
    question_type_order = ["글의 순서"]
    question_type_summary = ["요약문 완성"]
    question_type_long1 = ["기본 장문 독해"]
    question_type_long2 = ["복합 문단 독해"]

    question_content_text_map: Dict[str] = exam_question.question_content_text_map
    keys = list(question_content_text_map.keys())
    if exam_question.type in question_type_normal:
        big_text = question_content_text_map[keys[0]]
    elif exam_question.type in question_type_order:
        big_text = f"""
        {question_content_text_map[keys[0]]}\n\n
            
        (A) {question_content_text_map[keys[1]]}\n\n
        
        (B) {question_content_text_map[keys[2]]}\n\n
        
        (C) {question_content_text_map[keys[3]]}
        """
    elif exam_question.type in question_type_summary:
        big_text = f"""
        {question_content_text_map[keys[0]]}\n\n
        
        {question_content_text_map[keys[1]]}
        """
    elif exam_question.type in question_type_long1:
        big_text = question_content_text_map[keys[0]]
    elif exam_question.type in question_type_long2:
        big_text = f"""
        {question_content_text_map[keys[0]]}\n\n

        (A) {question_content_text_map[keys[1]]}\n\n

        (B) {question_content_text_map[keys[2]]}\n\n

        (C) {question_content_text_map[keys[3]]}
        """
    else:
        big_text = ""

    big_text = big_text.strip()
    big_text = big_text.replace("\n", "")

    return big_text


#
# ---------- HELPER FUNCTIONS ----------
#
def set_justification(paragraph, alignment="both"):
    p = paragraph._element
    pPr = p.get_or_add_pPr()
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), alignment)
    pPr.append(jc)


def add_formatted_text(paragraph, text):
    parts = re.split(r"(<\/?[biu]>)", text)
    formatting = {"b": False, "i": False, "u": False}

    for part in parts:
        if part in ("<b>", "</b>"):
            formatting["b"] = (part == "<b>")
        elif part in ("<i>", "</i>"):
            formatting["i"] = (part == "<i>")
        elif part in ("<u>", "</u>"):
            formatting["u"] = (part == "<u>")
        else:
            run = paragraph.add_run(part)
            run.font.bold = formatting["b"]
            run.font.italic = formatting["i"]
            run.font.underline = formatting["u"]
            run.font.name = font_name
            run.font.size = Pt(font_size)


def add_paragraph_with_alignment(cell: _Cell, text, alignment="both"):
    print(text.splitlines()[0])
    if len(text.splitlines()[0]) < 30 or re.match(r"^\s*\(?\d+\)", text):
        alignment = "left"
        print("[[align left]]")
    else:
        alignment = "both"
        print("[[align both]]")

    if cell.paragraphs and cell.paragraphs[0].text.strip() == "":
        p = cell.paragraphs[0]
    else:
        p = cell.add_paragraph()

    add_formatted_text(p, text)
    set_justification(p, alignment)
    return p


def split_text_by_lines(text: str,
                        max_lines: int = 20,
                        max_chars_per_line: int = 70) -> List[str]:

    raw_lines = []
    paragraphs = text.split("\n")
    for para in paragraphs:
        wrapped = textwrap.wrap(para, width=max_chars_per_line)
        if not wrapped:
            raw_lines.append("")
        else:
            raw_lines.extend(wrapped)

    chunks = []
    current_chunk = []
    for line in raw_lines:
        current_chunk.append(line)
        if len(current_chunk) >= max_lines:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
    # leftover
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def create_omml_element(latex_code):
    try:
        mathml = convert(latex_code)
    except Exception as e:
        raise ValueError(f"Error converting LaTeX to MathML: {e}")

    try:
        omml = mathml2omml.convert(mathml)
    except Exception as e:
        raise ValueError(f"Error converting MathML to OMML: {e}")

    if 'xmlns:m=' not in omml:
        omml = omml.replace(
            "<m:oMath",
            '<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
        )

    try:
        omml_element = etree.fromstring(omml.encode('utf-8'))
    except Exception as e:
        raise ValueError(f"Error parsing OMML: {e}")

    return omml_element


def insert_omml(paragraph, latex_code):
    omml_element = create_omml_element(latex_code)
    paragraph._element.append(omml_element)


class TableFlowManager:
    def __init__(self,
                 doc: Document,
                 max_lines_per_cell=20,
                 max_chars_per_line=70):
        self.doc = doc
        self.max_lines_per_cell = max_lines_per_cell
        self.max_chars_per_line = max_chars_per_line

        self.current_table = self._create_new_table()
        self.cell_order = [(0, 0), (1, 0), (0, 1), (1, 1)]
        self.cell_index = 0
        self.page_size = 1

    def _create_new_table(self):
        table = self.doc.add_table(rows=2, cols=2)
        table.autofit = False

        table.columns[0].width = Inches(3.75)
        table.columns[1].width = Inches(3.75)

        row_height_twips = 7150  # 12.62 cm in Twips
        for row in table.rows:
            tr = row._tr
            trHeight = OxmlElement('w:trHeight')
            trHeight.set(qn('w:val'), str(row_height_twips))
            trHeight.set(qn('w:hRule'), 'exact')
            tr.append(trHeight)

        return table

    def _start_new_page_and_table(self):
        if self.cell_index >= 4:
            self.current_table = self._create_new_table()
            self.cell_index = 0

    def _get_next_cell(self):
        if self.cell_index >= 4:
            self._start_new_page_and_table()

        r, c = self.cell_order[self.cell_index]
        self.cell_index += 1
        return r, c

    def add_question_to_cell(self,
                             question_text_list: List[Dict[str, str]],
                             answer_option_list: List[List[Dict[str, str]]]):
        def process_text_parts(target_paragraph, content_text, content_attributes):
            parts = re.split(latex_pattern, content_text)
            for idx, part_text in enumerate(parts):
                if idx % 2 == 0:
                    run = target_paragraph.add_run(part_text.rstrip("\n"))
                    if content_attributes.get('bold'):
                        run.bold = True
                    if content_attributes.get('underline'):
                        run.underline = True
                    if content_attributes.get('italic'):
                        run.italic = True
                else:
                    insert_omml(target_paragraph, part_text)

        r, c = self._get_next_cell()
        cell = self.current_table.cell(r, c)
        latex_pattern = r"\[:(.*?)\]"

        for question_text in question_text_list:
            text_content = question_text.get("insert", "")
            text_attributes = question_text.get("attributes", {})
            cell_paragraph = cell.paragraphs[0]
            process_text_parts(cell_paragraph, text_content, text_attributes)

        cell_paragraph.add_run("\n\n")

        for num, answer_option in enumerate(answer_option_list):
            for option_item in answer_option:
                option_text = f"({num + 1}) " + option_item.get("insert", "")
                option_text = option_text.replace("\n", "")
                option_attributes = option_item.get("attributes", {})
                process_text_parts(cell_paragraph, option_text, option_attributes)
                cell_paragraph.add_run("\n")

        if r == 1 and c == 1:
            self._start_new_page_and_table()

    def add_question(
            self,
            question_number: int,
            passage_text: str,
            subquestion_list: List[Tuple[str, List[str]]] = None
    ):
        if subquestion_list is None:
            subquestions = []

        for subquestion in subquestion_list:
            question_text_list: List[Dict[str, str]] = eval(
                subquestion[0].replace("true", "True").replace("false", "False")
            )
            question_text_list.insert(0, {"insert": f"{question_number}. "})

            answer_options_list: List[List[Dict[str, str]]] = [
                eval(i.replace("true", "True").replace("false", "False"))
                for i in subquestion[1]
            ]

            self.add_question_to_cell(question_text_list, answer_options_list)

