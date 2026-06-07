from __future__ import annotations
from collections import defaultdict
from datetime import timedelta
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from tp_manager.context_processors import current_tp_user
from tp_manager.models import TpUser, TPV2, TPV2CompetenceOfficielle, TPV2CritereOfficiel, SystemePedagogiqueRef, BacCompetence
from .forms import SequenceCreateForm, SequenceFormationForm, PresenceWaveForm, StudentGroupForm, GroupMemberForm, AssignmentForm, FreeChoiceFilterForm
from .models import SeqSequence, SeqWeeklySlot, SeqZone, SeqColoration, SeqSequenceFormation, SeqPresenceWave, SeqStudentGroup, SeqStudentGroupMember, SeqSession, SeqAssignment, SeqSystemBooking, SeqFreeChoiceRequest


def _is_prof(user):
    return bool(user and user.is_prof_like)


def _students():
    return TpUser.objects.filter(active=True).exclude(role_principal__in=['professeur','admin','admin_suite','responsable']).order_by('formation_code','class_name','last_name','first_name')


def _slot_date(start, week, slot):
    # date_debut is assumed to be in the same week; move to requested day number.
    # Python weekday Monday=0, our day Monday=1.
    monday = start - timedelta(days=start.weekday())
    return monday + timedelta(weeks=week - 1, days=(slot.day - 1))


def _generate_sessions(sequence, replace=False):
    slots = list(sequence.slots.filter(active=True).order_by('day', 'half_day'))
    if not slots and sequence.rotation_block_id:
        slots = list(sequence.rotation_block.slots.filter(active=True).order_by('day', 'half_day'))
    if not slots:
        slots = list(SeqWeeklySlot.objects.filter(active=True, day__in=[2,4,5]).order_by('day','half_day')[:3])
    if replace:
        sequence.sessions.all().delete()
    if sequence.sessions.exists() and not replace:
        return 0
    created = 0
    numero = 1
    for week in range(1, sequence.nb_semaines + 1):
        for slot in slots:
            SeqSession.objects.create(
                sequence=sequence,
                numero=numero,
                semaine=week,
                date=_slot_date(sequence.date_debut, week, slot),
                slot=slot,
                titre=f'S{week} — {slot}',
            )
            numero += 1
            created += 1
    return created


def dashboard(request):
    seqs = SeqSequence.objects.exclude(statut='archived')
    zones = SeqZone.objects.filter(active=True)
    formations = SeqSequenceFormation.objects.values('formation_code').annotate(count=Count('id')).order_by('formation_code')
    context = {
        'sequence_count': seqs.count(),
        'active_count': seqs.filter(statut='active').count(),
        'model_count': seqs.filter(sequence_modele=True).count(),
        'zone_count': zones.count(),
        'recent_sequences': seqs.select_related('zone_principale', 'coloration')[:8],
        'formations': formations,
    }
    return render(request, 'sequence_manager/dashboard.html', context)


def sequence_list(request):
    qs = SeqSequence.objects.select_related('zone_principale','coloration','rotation_block').prefetch_related('formations')
    zone = request.GET.get('zone')
    formation = request.GET.get('formation')
    coloration = request.GET.get('coloration')
    if zone:
        qs = qs.filter(Q(zone_principale_id=zone) | Q(zones__id=zone)).distinct()
    if formation:
        qs = qs.filter(formations__formation_code__iexact=formation).distinct()
    if coloration:
        qs = qs.filter(coloration_id=coloration)
    context = {
        'sequences': qs[:250],
        'zones': SeqZone.objects.filter(active=True),
        'colorations': SeqColoration.objects.filter(active=True),
        'formations': SeqSequenceFormation.objects.values_list('formation_code', flat=True).distinct().order_by('formation_code'),
        'filters': {'zone': zone or '', 'formation': formation or '', 'coloration': coloration or ''},
    }
    return render(request, 'sequence_manager/sequence_list.html', context)


def calendar(request):
    qs = SeqSequence.objects.exclude(statut='archived').select_related('zone_principale','coloration').prefetch_related('formations')
    zone = request.GET.get('zone')
    formation = request.GET.get('formation')
    if zone:
        qs = qs.filter(Q(zone_principale_id=zone) | Q(zones__id=zone)).distinct()
    if formation:
        qs = qs.filter(formations__formation_code__iexact=formation).distinct()
    blocks = []
    for seq in qs[:120]:
        counts = list(seq.formations.values('formation_code').annotate(total=Count('id'), effectif_total=Count('effectif')).order_by('formation_code'))
        effectifs = []
        for f in seq.formations.all():
            label = f'{f.formation_code} {f.effectif}' if f.effectif else f.formation_code
            if f.classe:
                label = f'{label} ({f.classe})'
            effectifs.append(label)
        blocks.append({'seq': seq, 'effectifs': effectifs})
    return render(request, 'sequence_manager/calendar.html', {
        'blocks': blocks,
        'zones': SeqZone.objects.filter(active=True),
        'formations': SeqSequenceFormation.objects.values_list('formation_code', flat=True).distinct().order_by('formation_code'),
        'filters': {'zone': zone or '', 'formation': formation or ''},
    })


def sequence_create(request):
    if request.method == 'POST':
        form = SequenceCreateForm(request.POST)
        if form.is_valid():
            seq = form.save()
            if seq.rotation_block_id:
                seq.slots.set(seq.rotation_block.slots.all())
                seq.zones.set(seq.rotation_block.zones.all())
                seq.professeurs.set(seq.rotation_block.professeurs.all())
                for rf in seq.rotation_block.formations.all():
                    SeqSequenceFormation.objects.get_or_create(sequence=seq, formation_code=rf.formation_code, classe=rf.classe, defaults={'niveau': rf.niveau, 'effectif': rf.effectif_prevu or 0})
            created = _generate_sessions(seq, replace=False)
            messages.success(request, f'Séquence créée. {created} séance(s) générée(s).')
            return redirect('sequence_manager:sequence_detail', pk=seq.pk)
    else:
        form = SequenceCreateForm()
    return render(request, 'sequence_manager/sequence_form.html', {'form': form})


def sequence_detail(request, pk):
    seq = get_object_or_404(SeqSequence.objects.select_related('zone_principale','coloration','rotation_block'), pk=pk)
    sessions = list(seq.sessions.prefetch_related('assignments__group__members__eleve', 'assignments__tp', 'assignments__systeme').all())
    groups = list(seq.student_groups.prefetch_related('members__eleve').all())
    # Build a template-friendly matrix. One row = one group/binôme/trinôme.
    assignments_by_group_session = defaultdict(lambda: defaultdict(list))
    individual_rows = {}
    for session in sessions:
        for assignment in session.assignments.all():
            if assignment.group_id:
                assignments_by_group_session[assignment.group_id][session.id].append(assignment)
            elif assignment.eleve_individuel_id:
                key = f'ind-{assignment.eleve_individuel_id}'
                individual_rows.setdefault(key, assignment.eleve_individuel)
                assignments_by_group_session[key][session.id].append(assignment)
    rows = []
    for group in groups:
        rows.append({'key': group.id, 'label': group.nom, 'group': group, 'cells': [{'session': s, 'assignments': assignments_by_group_session[group.id].get(s.id, [])} for s in sessions]})
    for key, eleve in individual_rows.items():
        rows.append({'key': key, 'label': eleve.full_name, 'group': None, 'cells': [{'session': s, 'assignments': assignments_by_group_session[key].get(s.id, [])} for s in sessions]})
    context = {'sequence': seq, 'sessions': sessions, 'groups': groups, 'rows': rows}
    return render(request, 'sequence_manager/sequence_detail.html', context)


def sequence_duplicate(request, pk):
    src = get_object_or_404(SeqSequence, pk=pk)
    new = SeqSequence.objects.create(
        titre=f'Copie — {src.titre}', description=src.description, rotation_block=src.rotation_block,
        zone_principale=src.zone_principale, coloration=src.coloration, axe_principal=src.axe_principal,
        date_debut=timezone.localdate(), nb_semaines=src.nb_semaines, statut='draft',
        auto_inscription_libre=src.auto_inscription_libre, validation_prof_requise=src.validation_prof_requise,
        notes_tp_activees=src.notes_tp_activees,
    )
    new.professeurs.set(src.professeurs.all())
    new.zones.set(src.zones.all())
    new.slots.set(src.slots.all())
    for f in src.formations.all():
        SeqSequenceFormation.objects.create(sequence=new, diplome=f.diplome, formation_code=f.formation_code, classe=f.classe, niveau=f.niveau, effectif=f.effectif)
    for old_s in src.sessions.all():
        SeqSession.objects.create(sequence=new, numero=old_s.numero, semaine=old_s.semaine, date=old_s.date, slot=old_s.slot, titre=old_s.titre)
    # Copy group patterns only, not pupils.
    group_map = {}
    for g in src.student_groups.all():
        ng = SeqStudentGroup.objects.create(sequence=new, nom=g.nom, type_groupe=g.type_groupe, formation_dominante=g.formation_dominante, ordre=g.ordre, parcours_libre=g.parcours_libre)
        group_map[g.id] = ng
    session_map = {s.numero: s for s in new.sessions.all()}
    for a in SeqAssignment.objects.filter(session__sequence=src).select_related('session'):
        ns = session_map.get(a.session.numero)
        if ns and a.group_id in group_map:
            SeqAssignment.objects.create(session=ns, group=group_map[a.group_id], tp=a.tp, systeme=a.systeme, zone=a.zone, professeur=a.professeur, mode=a.mode, status='planned', commentaire=a.commentaire, tp_note=a.tp_note, capacite_max=a.capacite_max)
    messages.success(request, 'Séquence dupliquée : structure, séances et TP conservés ; élèves réinitialisés.')
    return redirect('sequence_manager:sequence_detail', pk=new.pk)


def formation_add(request, pk):
    seq = get_object_or_404(SeqSequence, pk=pk)
    if request.method == 'POST':
        form = SequenceFormationForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False); obj.sequence = seq; obj.save()
            return redirect('sequence_manager:sequence_detail', pk=seq.pk)
    else:
        form = SequenceFormationForm()
    return render(request, 'sequence_manager/simple_form.html', {'form': form, 'title': 'Ajouter une formation / classe', 'sequence': seq})


def wave_add(request, pk):
    seq = get_object_or_404(SeqSequence, pk=pk)
    formation_code = request.GET.get('formation') or None
    classe = request.GET.get('classe') or None
    if request.method == 'POST':
        form = PresenceWaveForm(request.POST, formation_code=formation_code, classe=classe)
        if form.is_valid():
            obj = form.save(commit=False); obj.sequence = seq; obj.save(); form.save_m2m()
            return redirect('sequence_manager:sequence_detail', pk=seq.pk)
    else:
        form = PresenceWaveForm(formation_code=formation_code, classe=classe)
    return render(request, 'sequence_manager/simple_form.html', {'form': form, 'title': 'Ajouter une vague / présence élèves', 'sequence': seq})


def group_add(request, pk):
    seq = get_object_or_404(SeqSequence, pk=pk)
    if request.method == 'POST':
        form = StudentGroupForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False); obj.sequence = seq; obj.save()
            return redirect('sequence_manager:group_members', pk=obj.pk)
    else:
        form = StudentGroupForm()
        form.fields['wave'].queryset = seq.waves.all()
    return render(request, 'sequence_manager/simple_form.html', {'form': form, 'title': 'Créer un binôme / trinôme / groupe', 'sequence': seq})


def group_members(request, pk):
    group = get_object_or_404(SeqStudentGroup.objects.select_related('sequence'), pk=pk)
    if request.method == 'POST':
        form = GroupMemberForm(request.POST, sequence=group.sequence)
        if form.is_valid():
            group.members.all().delete()
            for i, eleve in enumerate(form.cleaned_data['eleves'], 1):
                SeqStudentGroupMember.objects.create(group=group, eleve=eleve, ordre=i)
            return redirect('sequence_manager:sequence_detail', pk=group.sequence.pk)
    else:
        form = GroupMemberForm(sequence=group.sequence)
        form.fields['eleves'].initial = list(group.members.values_list('eleve_id', flat=True))
    return render(request, 'sequence_manager/simple_form.html', {'form': form, 'title': f'Membres de {group.nom}', 'sequence': group.sequence})


def sessions_generate(request, pk):
    seq = get_object_or_404(SeqSequence, pk=pk)
    created = _generate_sessions(seq, replace=request.POST.get('replace') == '1')
    messages.success(request, f'{created} séance(s) générée(s).')
    return redirect('sequence_manager:sequence_detail', pk=seq.pk)


def assignment_add(request, pk):
    seq = get_object_or_404(SeqSequence, pk=pk)
    if request.method == 'POST':
        form = AssignmentForm(request.POST, sequence=seq)
        if form.is_valid():
            obj = form.save()
            if obj.systeme_id:
                SeqSystemBooking.objects.get_or_create(sequence=seq, session=obj.session, assignment=obj, systeme=obj.systeme, defaults={'status': 'reserved', 'source': 'sequence'})
            return redirect('sequence_manager:sequence_detail', pk=seq.pk)
    else:
        initial = {'session': request.GET.get('session'), 'group': request.GET.get('group')}
        form = AssignmentForm(sequence=seq, initial=initial)
    return render(request, 'sequence_manager/simple_form.html', {'form': form, 'title': 'Ajouter une affectation TP / système', 'sequence': seq})


def free_choice(request, pk):
    seq = get_object_or_404(SeqSequence, pk=pk)
    form = FreeChoiceFilterForm(request.GET or None)
    tps = TPV2.objects.exclude(statut='archive').select_related('diplome')
    if form.is_valid():
        if form.cleaned_data.get('diplome'):
            tps = tps.filter(diplome=form.cleaned_data['diplome'])
        theme = form.cleaned_data.get('theme')
        if theme:
            tps = tps.filter(Q(domaine_principal__icontains=theme) | Q(sous_theme__icontains=theme) | Q(mots_cles__icontains=theme))
        comp = form.cleaned_data.get('competence')
        if comp:
            tps = tps.filter(competences_officielles__competence__code__icontains=comp).distinct()
    return render(request, 'sequence_manager/free_choice.html', {'sequence': seq, 'form': form, 'tps': tps[:80]})


def skills_by_class(request, pk):
    seq = get_object_or_404(SeqSequence, pk=pk)
    mode = request.GET.get('mode', 'compact')
    rows = defaultdict(lambda: defaultdict(list))
    assignments = SeqAssignment.objects.filter(session__sequence=seq, tp__isnull=False).select_related('tp__diplome')
    for assignment in assignments:
        # determine classes involved by group members or individual
        classes = set()
        if assignment.group_id:
            for m in assignment.group.members.select_related('eleve'):
                e = m.eleve
                classes.add((e.formation_code or assignment.tp.diplome.code, e.class_name or 'Sans classe'))
        elif assignment.eleve_individuel_id:
            e = assignment.eleve_individuel
            classes.add((e.formation_code or assignment.tp.diplome.code, e.class_name or 'Sans classe'))
        if not classes:
            classes.add((assignment.tp.diplome.code, 'Élève type'))
        for link in assignment.tp.competences_officielles.select_related('competence'):
            comp = link.competence
            criteria = list(assignment.tp.criteres_officiels_selectionnes.filter(critere__competence=comp).select_related('critere'))
            for key in classes:
                rows[key][comp].append({'tp': assignment.tp, 'type_lien': link.type_lien, 'criteria': [c.critere for c in criteria]})
    return render(request, 'sequence_manager/skills_by_class.html', {'sequence': seq, 'mode': mode, 'rows': sorted(rows.items())})
