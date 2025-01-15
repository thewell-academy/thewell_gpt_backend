from typing import List, Dict, Tuple
from docx import Document
from docx.shared import Pt, Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import textwrap
import re

from docx.table import _Cell

from database.models.exam_question import ExamQuestion

font_name = "Times New Roman"
font_size = 9


def get_big_text(exam_question: ExamQuestion):
    question_type_normal = ["글의 목적", "글의 분위기 / 심경", "대의 파악", "함의 추론", "도표 이해", "내용 일치 / 불일치", "실용문 일치 / 불일치", "어법성 판단",
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
    """
    Sets text justification for the given paragraph.
    - 'both': Full justification (default)
    - 'left': Left-aligned
    """
    p = paragraph._element
    pPr = p.get_or_add_pPr()
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), alignment)
    pPr.append(jc)


def add_formatted_text(paragraph, text):
    """
    Allows <b>, <i>, <u> inline tags in 'text',
    applying the corresponding run-level formatting.
    """
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
    """
    Adds text to a cell with conditional alignment.
    - Use full justification ('both') for long blocks of text.
    - Use left alignment ('left') for short text like titles or options.
    """
    # Determine alignment based on content
    print(text.splitlines()[0])
    if len(text.splitlines()[0]) < 30 or re.match(r"^\s*\(?\d+\)", text):
        alignment = "left"
        print("[[align left]]")
    else:
        alignment = "both"
        print("[[align both]]")

    # Use existing paragraph if available
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
    """
    Splits 'text' into 'chunks' approximating a fixed cell height:
      - up to 'max_lines' lines per chunk,
      - each line up to 'max_chars_per_line' characters.

    We do a word-wrap of each paragraph at 'max_chars_per_line',
    then group lines in sets of up to 'max_lines'.
    """
    raw_lines = []
    paragraphs = text.split("\n")
    for para in paragraphs:
        wrapped = textwrap.wrap(para, width=max_chars_per_line)
        if not wrapped:
            raw_lines.append("")  # keep blank line
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


#
# ---------- TABLE FLOW MANAGER ----------
#

class TableFlowManager:
    """
    We have a 2×2 table, fill cells in order:
        (0,0) -> (1,0) -> (0,1) -> (1,1).
    If we place a chunk in (1,1) and still have leftover,
    we do a new page and continue from (0,0).

    We combine question text, big_text, subquestions+answers
    into a single string, then chunk it all at once.
    """

    def __init__(self,
                 doc: Document,
                 max_lines_per_cell=20,
                 max_chars_per_line=70):
        self.doc = doc
        self.max_lines_per_cell = max_lines_per_cell
        self.max_chars_per_line = max_chars_per_line

        self.current_table = self._create_new_table()
        self.cell_order = [(0, 0), (1, 0), (0, 1), (1, 1)]
        self.cell_index = 0  # 0..3
        self.page_size = 1

    def _create_new_table(self):
        table = self.doc.add_table(rows=2, cols=2)
        table.autofit = False  # Disable autofit for manual control

        # Set column widths
        table.columns[0].width = Inches(3.75)
        table.columns[1].width = Inches(3.75)

        # Set each row height to 12.62 cm (approximately 7150 Twips)
        row_height_twips = 7150  # 12.62 cm in Twips
        for row in table.rows:
            tr = row._tr
            trHeight = OxmlElement('w:trHeight')
            trHeight.set(qn('w:val'), str(row_height_twips))  # Fixed height in Twips
            trHeight.set(qn('w:hRule'), 'exact')  # Set exact height rule
            tr.append(trHeight)

        return table

    def _start_new_page_and_table(self):
        """
        Force a page break, create a fresh 2×2 table,
        reset cell_index=0. Ensures no unnecessary blank pages occur.
        """
        # Check if the current table has been filled completely
        if self.cell_index >= 4:
            # self.doc.add_page_break()  # Add a page break only if needed
            self.current_table = self._create_new_table()
            self.cell_index = 0

    def _get_next_cell(self):
        """
        Return the cell coords (r, c) for the next chunk.
        If we've used all 4 cells, start a new page (0,0).
        """
        if self.cell_index >= 4:
            self._start_new_page_and_table()

        r, c = self.cell_order[self.cell_index]
        self.cell_index += 1
        return r, c

    def add_question(
            self,
            big_text: str,
            subquestions: List[Tuple[str, List[str]]] = None
    ):
        if subquestions is None:
            subquestions = []

        combined_str = subquestions[0][0] if len(subquestions) == 1 else "다음을 읽고 물음에 답하시오."
        combined_str = combined_str.strip()
        combined_str += "\n" + big_text + "\n"

        for (subq, answers) in subquestions:
            # subquestion text
            if len(subquestions) > 1:
                combined_str += f"\n\n{subq.strip()}"
            # if we have answers, we can do e.g.:
            if answers:
                combined_str += "\n"  # line break
                for idx, ans in enumerate(answers, 1):
                    combined_str += f"({idx}) {ans.strip()}\n"
                # remove final newline if you want
                combined_str = combined_str.rstrip("\n")

        chunks = split_text_by_lines(
            combined_str,
            self.max_lines_per_cell,
            self.max_chars_per_line
        )

        chunk_index = 0
        chunks_size = len(chunks)

        while chunk_index < chunks_size:
            r, c = self._get_next_cell()
            cell = self.current_table.cell(r, c)

            chunk = chunks[chunk_index]

            # 만약 merge해야 한다면 merge 후 cell 전달
            if chunk_index < chunks_size - 1:
                if r == 0 and c == 0:
                    top_left_cell = self.current_table.cell(0, 0)
                    bottom_left_cell = self.current_table.cell(1, 0)
                    top_left_cell._tc.merge(bottom_left_cell._tc)  # merges vertically
                    cell = top_left_cell
                    chunk_index += 1
                    chunk += chunks[chunk_index]

                elif r == 0 and c == 1:
                    top_right_cell = self.current_table.cell(0, 1)
                    bottom_right_cell = self.current_table.cell(1, 1)
                    top_right_cell._tc.merge(bottom_right_cell._tc)  # merges vertically
                    cell = top_right_cell
                    chunk_index += 1
                    chunk += chunks[chunk_index]

            add_paragraph_with_alignment(cell, chunk, "both")

            # if we're at bottom-right and still leftover, new page
            is_bottom_right = (r == 1 and c == 1)
            still_leftover = (chunk_index < chunks_size - 1)
            if is_bottom_right and still_leftover:
                self._start_new_page_and_table()

            chunk_index += 1
