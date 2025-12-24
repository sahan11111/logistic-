from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_invoice_pdf(invoice, file_path):
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Logistics Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Invoice No: {invoice.invoice_number}")
    c.drawString(50, height - 130, f"Order Token: {invoice.order.token}")
    c.drawString(50, height - 160, f"Customer: {invoice.order.customer.username}")
    c.drawString(50, height - 190, f"Amount: Rs. {invoice.amount}")
    c.drawString(50, height - 220, f"Date: {invoice.generated_at.date()}")

    c.showPage()
    c.save()
