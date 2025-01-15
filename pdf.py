from fpdf import FPDF

# Initialize the PDF
pdf = FPDF()
pdf.add_page()

# Set font (Arial is a built-in font in FPDF)
pdf.set_font("Arial", size=12)

# Add a title
pdf.cell(0, 10, "Generated PDF", ln=True, align="C")
pdf.ln(10)

# Add question text
question_number = "21"
question_text = "밑줄 친 hunting the shadow, not the substance가 다음 글에서 의미하는 바로 가장 적절한 것은?"
pdf.multi_cell(0, 8, f"{question_number}. {question_text}")
pdf.ln(5)

# Add paragraph
paragraph = (
    "The position of the architect rose during the Roman Empire, as architecture symbolically "
    "became a particularly important political statement. Cicero classed the architect with the "
    "physician and the teacher and Vitruvius spoke of 'so great a profession as this.' Marcus Vitruvius "
    "Pollio, a practicing architect during the rule of Augustus Caesar, recognized that architecture requires "
    "both practical and theoretical knowledge, and he listed the disciplines he felt the aspiring architect "
    "should master: literature and writing, draftsmanship, mathematics, history, philosophy, music, medicine, "
    "law, and astronomy—a curriculum that still has much to recommend it. All of this study was necessary, "
    "he argued, because architects who have aimed at acquiring manual skill without scholarship have never "
    "been able to reach a position of authority to correspond to their plans, while those who have relied only "
    "upon theories and scholarship were obviously 'hunting the shadow, not the substance.'"
)
pdf.set_font("Arial", size=11)
pdf.multi_cell(0, 8, paragraph)
pdf.ln(5)

# Add options
options = [
    "seeking abstract knowledge emphasized by architectural tradition",
    "discounting the subjects necessary to achieve architectural goals",
    "pursuing the ideals of architecture without the practical skills",
    "prioritizing architecture’s material aspects over its artistic ones",
    "following historical precedents without regard to current standards",
]
for idx, option in enumerate(options, 1):
    pdf.cell(0, 10, f"    {idx}) {option}", ln=True)

# Save the PDF
pdf_output_path = "question_output.pdf"
pdf.output(pdf_output_path)

print(f"PDF generated and saved as {pdf_output_path}")