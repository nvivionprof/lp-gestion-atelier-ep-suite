import tempfile

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse
from django.shortcuts import render, redirect

from .management.commands.suite_xlsx import export_xlsx, import_xlsx


@staff_member_required
def suite_xlsx_page(request):
    if request.method == "POST":
        action = request.POST.get("action")

        if action in {"template", "export"}:
            template = action == "template"
            suffix = "modele" if template else "export"

            tmp = tempfile.NamedTemporaryFile(
                prefix=f"toolmag_{suffix}_",
                suffix=".xlsx",
                delete=False,
            )
            tmp.close()

            export_xlsx(tmp.name, template=template)

            return FileResponse(
                open(tmp.name, "rb"),
                as_attachment=True,
                filename=f"toolmag_{suffix}.xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        if action == "import":
            uploaded = request.FILES.get("xlsx_file")
            dry_run = request.POST.get("dry_run") == "on"

            if not uploaded:
                messages.error(request, "Aucun fichier XLSX fourni.")
                return redirect(request.path)

            tmp = tempfile.NamedTemporaryFile(
                prefix="toolmag_import_",
                suffix=".xlsx",
                delete=False,
            )

            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp.close()

            try:
                created, updated, m2m = import_xlsx(tmp.name, dry_run=dry_run)
            except Exception as exc:
                messages.error(request, f"Import impossible : {exc}")
                return redirect(request.path)

            if dry_run:
                messages.warning(
                    request,
                    f"Simulation terminée : {created} création(s), {updated} mise(s) à jour, {m2m} relation(s) M2M. Aucune donnée écrite."
                )
            else:
                messages.success(
                    request,
                    f"Import terminé : {created} création(s), {updated} mise(s) à jour, {m2m} relation(s) M2M."
                )

            return redirect(request.path)

    return render(request, "inventory/suite_xlsx.html", {"module_name": "ToolMag"})
