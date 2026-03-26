"""Generate a professional financial report PDF for Matt Anthony Photography."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpdf import FPDF
from datetime import date

class FinanceReport(FPDF):
    # Colors
    NAVY = (39, 44, 57)
    BLUE = (57, 113, 222)
    GREEN = (30, 159, 108)
    RED = (217, 51, 51)
    ORANGE = (230, 136, 30)
    PURPLE = (124, 81, 205)
    GRAY = (140, 146, 156)
    LIGHT = (247, 248, 250)
    WHITE = (255, 255, 255)
    DARK = (25, 29, 38)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*self.GRAY)
            self.cell(0, 8, "Matt Anthony Photography  |  Financial Report  |  March 2026", align="R")
            self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, f"Confidential  |  Prepared March 20, 2026  |  Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title, color=None):
        if color is None: color = self.NAVY
        self.ln(6)
        self.set_fill_color(*color)
        self.set_text_color(*self.WHITE)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_text_color(*self.DARK)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.NAVY)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def kpi_row(self, items):
        """items = [(label, value, color), ...]"""
        w = (self.w - 20) / len(items)
        y = self.get_y()
        for label, value, color in items:
            x = self.get_x()
            # Card background
            self.set_fill_color(245, 246, 248)
            self.rect(x, y, w - 3, 22, "F")
            # Top accent
            self.set_fill_color(*color)
            self.rect(x, y, w - 3, 2.5, "F")
            # Label
            self.set_xy(x + 3, y + 4)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*self.GRAY)
            self.cell(w - 9, 4, label)
            # Value
            self.set_xy(x + 3, y + 9)
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*color)
            self.cell(w - 9, 8, value)
            self.set_xy(x + w, y)
        self.set_y(y + 26)
        self.set_text_color(*self.DARK)

    def table_header(self, cols, widths):
        self.set_fill_color(*self.LIGHT)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*self.GRAY)
        for col, w in zip(cols, widths):
            align = "R" if any(c in col for c in ["$", "%", "Amount", "Total", "Rate", "Avg"]) else "L"
            self.cell(w, 7, col, fill=True, align=align)
        self.ln()
        # Bottom line
        self.set_draw_color(*self.GRAY)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1)

    def table_row(self, cells, widths, bold=False, bg=None, text_colors=None):
        if bg:
            self.set_fill_color(*bg)
            fill = True
        else:
            fill = False
        self.set_font("Helvetica", "B" if bold else "", 8)
        self.set_text_color(*self.DARK)
        for i, (cell, w) in enumerate(zip(cells, widths)):
            if text_colors and i < len(text_colors) and text_colors[i]:
                self.set_text_color(*text_colors[i])
            align = "R" if i > 0 and any(c in str(cell) for c in ["$", "%", "-"]) else "L"
            self.cell(w, 6, str(cell), fill=fill, align=align)
            self.set_text_color(*self.DARK)
        self.ln()

    def bullet(self, text, bold_prefix=""):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*self.DARK)
        x = self.get_x()
        self.cell(5, 5, "-")
        if bold_prefix:
            self.set_font("Helvetica", "B", 8)
            self.cell(self.get_string_width(bold_prefix) + 1, 5, bold_prefix)
            self.set_font("Helvetica", "", 8)
        self.multi_cell(self.w - self.r_margin - self.get_x(), 5, text)


def generate():
    pdf = FinanceReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(True, margin=20)
    pdf.set_margins(10, 10, 10)

    # -- COVER PAGE --
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*FinanceReport.NAVY)
    pdf.cell(0, 15, "Financial Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*FinanceReport.GRAY)
    pdf.cell(0, 10, "Matt Anthony Photography", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(*FinanceReport.BLUE)
    pdf.line(70, pdf.get_y(), 140, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "2024  ·  2025  ·  2026 (Q1)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Prepared March 20, 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sole Proprietor  ·  Squamish, BC  ·  GST Registered", align="C", new_x="LMARGIN", new_y="NEXT")

    # -- PAGE 2: EXECUTIVE SUMMARY --
    pdf.add_page()
    pdf.section_title("EXECUTIVE SUMMARY")

    pdf.kpi_row([
        ("2025 Revenue", "$102,573", FinanceReport.BLUE),
        ("2025 Net Profit", "-$3,634", FinanceReport.RED),
        ("2025 Tax + CPP", "$6,816", FinanceReport.ORANGE),
        ("Tax Savings", "$6,893", FinanceReport.GREEN),
    ])

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*FinanceReport.DARK)
    pdf.multi_cell(0, 5, "Revenue grew 37% year-over-year ($75K -> $103K), driven by expanded client base and retainer model. Business expenses were elevated due to $58K in equipment purchases (camera bodies, lenses, drone) which are recovered over multiple years through CCA depreciation. Tax was optimized from $13,709 to $6,816 through CCA with Accelerated Investment Incentive, CRA mileage method (20,000 km), 50% home office deduction, and strategic meal categorization.")
    pdf.ln(4)

    pdf.sub_title("Three-Year Revenue Trajectory")
    w = [50, 35, 35, 35]
    pdf.table_header(["Year", "Revenue", "Growth", "Monthly Avg"], w)
    pdf.table_row(["2024 (filed)", "$75,017", "-", "$6,251"], w)
    pdf.table_row(["2025", "$102,573", "+37%", "$8,548"], w)
    pdf.table_row(["2026 (Q1)", "$5,945", "-", "$1,982"], w)
    pdf.table_row(["2026 Target", "$172,900", "+69%", "$14,408"], w, bold=True, bg=(235, 240, 252))

    # -- PAGE 3: 2025 P&L --
    pdf.add_page()
    pdf.section_title("2025 PROFIT & LOSS")

    pdf.kpi_row([
        ("Revenue", "$102,573", FinanceReport.BLUE),
        ("Business Expenses", "$106,207", FinanceReport.RED),
        ("Personal Expenses", "$78,957", FinanceReport.PURPLE),
    ])

    pdf.sub_title("Monthly Performance")
    w = [25, 30, 30, 30, 20]
    pdf.table_header(["Month", "Revenue", "Expenses", "Net", "Margin"], w)
    months_data = [
        ("Jan", "$5,388", "$4,402", "$986", "18%"),
        ("Feb", "$7,827", "$3,870", "$3,957", "51%"),
        ("Mar", "$5,434", "$4,094", "$1,339", "25%"),
        ("Apr", "$14,390", "$3,074", "$11,317", "79%"),
        ("May", "$9,132", "$18,641", "-$9,509", "-104%"),
        ("Jun", "$3,719", "$8,212", "-$4,493", "-121%"),
        ("Jul", "$14,660", "$4,743", "$9,917", "68%"),
        ("Aug", "$9,708", "$37,399", "-$27,691", "-285%"),
        ("Sep", "$8,005", "$4,228", "$3,777", "47%"),
        ("Oct", "$9,867", "$6,641", "$3,227", "33%"),
        ("Nov", "$12,438", "$3,916", "$8,521", "69%"),
        ("Dec", "$2,004", "$5,359", "-$3,354", "-167%"),
    ]
    for i, row in enumerate(months_data):
        net_color = FinanceReport.GREEN if "-" not in row[3] else FinanceReport.RED
        bg = FinanceReport.LIGHT if i % 2 == 0 else None
        pdf.table_row(row, w, bg=bg, text_colors=[None, FinanceReport.BLUE, FinanceReport.RED, net_color, None])
    pdf.table_row(["TOTAL", "$102,573", "$104,578", "-$2,005", "-2%"], w, bold=True, bg=(235, 240, 252))

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*FinanceReport.GRAY)
    pdf.cell(0, 5, "Note: May and Aug deficits driven by Camera Canada ($10.7K) and Amazon equipment purchases.", new_x="LMARGIN", new_y="NEXT")

    # -- PAGE 4: BUSINESS EXPENSES --
    pdf.add_page()
    pdf.section_title("2025 BUSINESS EXPENSES - T2125", FinanceReport.ORANGE)

    w = [60, 25, 35, 35]
    pdf.table_header(["CRA Category", "Line", "Amount", "% of Revenue"], w)
    expenses = [
        ("Equipment (CCA)", "9936", "$57,791", "56.3%"),
        ("Office Supplies (<$500)", "8811", "$11,085", "10.8%"),
        ("Rent / Co-working", "8860", "$9,251", "9.0%"),
        ("Software & Subscriptions", "8871", "$7,989", "7.8%"),
        ("Vehicle", "8615", "$5,234", "5.1%"),
        ("Meals & Entertainment", "9270", "$4,542", "4.4%"),
        ("Advertising & Marketing", "8521", "$3,942", "3.8%"),
        ("Travel", "8910", "$1,323", "1.3%"),
        ("Telephone & Internet", "8945", "$1,250", "1.2%"),
        ("Clothing (Business)", "-", "$1,213", "1.2%"),
        ("Insurance", "8690", "$678", "0.7%"),
        ("Interest & Bank Charges", "8710", "$660", "0.6%"),
        ("Professional Fees", "8590", "$146", "0.1%"),
    ]
    for i, row in enumerate(expenses):
        bg = FinanceReport.LIGHT if i % 2 == 0 else None
        pdf.table_row(row, w, bg=bg)

    # -- PAGE 5: TAX OPTIMIZATION --
    pdf.add_page()
    pdf.section_title("2025 TAX OPTIMIZATION", FinanceReport.GREEN)

    pdf.kpi_row([
        ("Original Tax Estimate", "$13,709", FinanceReport.RED),
        ("Optimized Tax", "$6,816", FinanceReport.GREEN),
        ("You Saved", "$6,893", FinanceReport.GREEN),
    ])

    pdf.sub_title("Optimizations Applied")
    w = [70, 35, 40]
    pdf.table_header(["Strategy", "Deduction", "Tax Saved"], w)
    opts = [
        ("CCA with AII (Accelerated Investment Incentive)", "$12,816", "~$3,600"),
        ("Vehicle - CRA Mileage Method (20,000 km)", "$13,500", "~$3,800"),
        ("Home Office - 50% of rent ($1,100/mo all-in)", "$4,350", "~$1,200"),
        ("Client & Travel Meals (50% deductible)", "$2,914", "~$400"),
        ("CPP 50% Deduction (Line 22200)", "$2,548", "~$580"),
        ("Correct BPA Credits (Fed + BC)", "-", "~$100"),
    ]
    for i, row in enumerate(opts):
        bg = FinanceReport.LIGHT if i % 2 == 0 else None
        pdf.table_row(row, w, bg=bg)

    pdf.ln(4)
    pdf.sub_title("Tax Summary")
    w = [80, 40]
    pdf.table_header(["Line Item", "Amount"], w)
    tax_lines = [
        ("Gross Business Income", "$102,573"),
        ("T2125 Expenses (incl CCA + Home Office)", "$69,267"),
        ("Net Business Income", "$33,306"),
        ("CPP Deduction (50%)", "-$2,548"),
        ("Adjusted Net Income", "$30,758"),
        ("Federal Tax", "$2,194"),
        ("BC Provincial Tax", "$1,396"),
        ("CPP Self-Employed", "$3,226"),
    ]
    for row in tax_lines:
        pdf.table_row(row, w)
    pdf.table_row(("TOTAL TAX + CPP", "$6,816"), w, bold=True, bg=(230, 247, 240), text_colors=[FinanceReport.GREEN, FinanceReport.GREEN])

    # -- PAGE 6: GST --
    pdf.ln(4)
    pdf.sub_title("GST Summary (Canadian ITCs Only)")
    w = [40, 25, 25, 25, 25, 25]
    pdf.table_header(["", "Q1", "Q2", "Q3", "Q4", "YTD"], w)
    pdf.table_row(["Collected", "$888", "$1,297", "$1,542", "$1,158", "$4,884"], w, text_colors=[None]+[FinanceReport.GREEN]*5)
    pdf.table_row(["ITCs", "$439", "$1,347", "$2,144", "$689", "$4,619"], w, text_colors=[None]+[FinanceReport.RED]*5)
    pdf.table_row(["Net Owing", "$449", "-$50", "-$602", "$469", "$266"], w, bold=True, bg=(253, 237, 237))

    # -- PAGE 7: RECOMMENDATIONS --
    pdf.add_page()
    pdf.section_title("RECOMMENDATIONS", FinanceReport.BLUE)

    pdf.sub_title("Immediate Actions")
    pdf.ln(2)
    pdf.bullet("Open a First Home Savings Account (FHSA) before Dec 31, 2026. $8,000/yr tax deduction with tax-free growth. At your rate, saves ~$2,200/yr.", "1. FHSA - ")
    pdf.ln(1)
    pdf.bullet("Max RRSP contribution before March 2027. Room: ~$10K. Every $1,000 saves ~$280 in tax. Use Questrade.", "2. RRSP - ")
    pdf.ln(1)
    pdf.bullet("Redirect Shakepay crypto to FHSA -> RRSP -> TFSA. These have tax advantages; crypto doesn't.", "3. Redirect Investments - ")
    pdf.ln(1)
    pdf.bullet("Elect GST Quick Method for 2027. Photography services remit 3.6% instead of 5%. Saves ~$1,000+/yr.", "4. GST Quick Method - ")

    pdf.ln(3)
    pdf.sub_title("Spending Control")
    pdf.ln(2)
    pdf.bullet("Your AOS targets $3K/mo owner draw. You spent $6,580/mo in 2025. Cut to $3,000/mo to stop bleeding cash.", "5. Personal Budget - ")
    pdf.ln(1)
    pdf.bullet("Review $8K/yr software stack. Cold email tools (LeadGenJay + Instantly + IcyPeas) cost $2,673/yr. Evaluate ROI.", "6. Software Audit - ")
    pdf.ln(1)
    pdf.bullet("Move ALL business to business card/chequing. Personal card = personal only. Simplifies everything.", "7. Separate Accounts - ")

    pdf.ln(3)
    pdf.sub_title("Revenue Growth")
    pdf.ln(2)
    pdf.bullet("Q1 run rate is $24K - far below $173K target. You need $18,500/mo for remaining 9 months. Focus on retainer clients.", "8. Close Revenue Gap - ")
    pdf.ln(1)
    pdf.bullet("2 retainer clients at $2,500-3,000/mo = $60K in recurring annual revenue.", "9. Retainer Model - ")
    pdf.ln(1)
    pdf.bullet("At $173K revenue, incorporation saves ~$2,500/yr in CPP plus tax deferral. Discuss with accountant.", "10. Consider Incorporating - ")

    pdf.ln(4)
    pdf.sub_title("2026 Monthly Budget")
    w = [70, 40]
    pdf.table_header(["Item", "Monthly"], w)
    budget = [
        ("Revenue target", "$14,400"),
        ("Business expenses", "-$4,500"),
        ("Tax set-aside (25%)", "-$3,600"),
        ("Owner draw (your pay)", "-$3,000"),
        ("FHSA contribution", "-$667"),
        ("RRSP contribution", "-$833"),
        ("Emergency fund", "-$500"),
    ]
    for row in budget:
        pdf.table_row(row, w)
    pdf.table_row(("Surplus -> TFSA or reinvest", "$1,300"), w, bold=True, bg=(230, 247, 240), text_colors=[FinanceReport.GREEN, FinanceReport.GREEN])

    # -- PAGE 8: 2026 Q1 --
    pdf.add_page()
    pdf.section_title("2026 Q1 SNAPSHOT")

    pdf.kpi_row([
        ("Q1 Revenue", "$5,945", FinanceReport.BLUE),
        ("Q1 Biz Expenses", "$9,193", FinanceReport.RED),
        ("Q1 Net", "-$3,248", FinanceReport.RED),
        ("Tax Owing (YTD)", "$0", FinanceReport.GREEN),
    ])

    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, "Q1 shows a net loss which is typical - annual subscriptions and equipment financing (Affirm) are front-loaded while revenue ramps up. CCA ($7,525) and home office ($6,600) further reduce taxable income. No tax owing yet. As client revenue accelerates through Q2-Q4, the numbers will normalize.")

    pdf.ln(4)
    pdf.sub_title("Asia Trip Cost (Jan 5 - Mar 5)")
    w = [70, 35]
    pdf.table_header(["Category", "Amount"], w)
    trip = [
        ("Accommodation (Airbnb + guesthouses)", "$2,300"),
        ("Flights (AirAsia × 2 + Cathay Pacific)", "$1,824"),
        ("Software (running while abroad)", "$1,896"),
        ("Equipment (Affirm payments)", "$1,897"),
        ("Food & Dining", "$516"),
        ("Local Transport (Grab/Uber)", "$162"),
        ("eSIMs + Visa fees", "$320"),
        ("ATM Cash (Bali/Sri Lanka spending)", "$3,400"),
    ]
    for row in trip:
        pdf.table_row(row, w)
    pdf.table_row(("TOTAL (59 days = $284/day)", "$16,743"), w, bold=True, bg=(235, 240, 252))

    # -- SAVE --
    output_path = "/Users/matthewfernandes/Downloads/Matt Anthony - Financial Report 2025-2026.pdf"
    pdf.output(output_path)
    print(f"PDF saved: {output_path}")
    return output_path

if __name__ == "__main__":
    generate()
