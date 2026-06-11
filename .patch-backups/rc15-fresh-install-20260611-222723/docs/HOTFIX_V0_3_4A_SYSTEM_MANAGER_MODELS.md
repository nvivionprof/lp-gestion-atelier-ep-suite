# Hotfix V0.3.4a — System Manager models

Correction du crash au démarrage de System Manager :

```text
NameError: name 'WorkshopBlock' is not defined
```

Cause : `ReservationGroup` référençait `WorkshopBlock` et `WorkshopBlockSlot` avant leur déclaration dans `models.py`.

Correction : passage en références différées Django :

```python
models.ForeignKey('WorkshopBlock', ...)
models.ManyToManyField('WorkshopBlockSlot', ...)
```

Ce correctif ne modifie pas les bases de données existantes et ne touche pas TP Manager.
