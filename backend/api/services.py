from django.template.loader import get_template
from django.utils import timezone
from weasyprint import HTML


def pdf_over_template(request, template_location: str, context: dict) -> dict:
    template = get_template(template_location)
    html_string = template.render(context, request=request)
    pdf = HTML(string=html_string).write_pdf()
    time = timezone.now()
    filename = f"shopping_list_{time}.pdf"

    pdf_data = dict(pdf=pdf, filename=filename)
    return pdf_data
