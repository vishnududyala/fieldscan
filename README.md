# FieldScan

Point it at a construction/site photo, it drafts the observation instead of
you typing it out.

## why

Apps like ArchiSnapper are great for the annotation + PDF report side of
field inspections, but someone still has to look at every photo and type
what's wrong, how bad it is, what category. That's the part this attacks.

Went through Deltek's public AI stuff (Dela, GovWin's Smart Fit Score, Ask
Dela) and all of it is text/data based, summarizing docs, scoring leads,
answering questions. Didn't find anything that actually looks at a photo.
Could easily be wrong, only public info here, no idea what they have
internally.

Built this with a decent amount of Claude's help, mainly the vision prompt
and the initial script structure, then went back and fixed things by hand
(the image format bug below was a real bug I hit, not scripted).

## what it does

- looks at a photo
- writes a 2-3 sentence description of what's wrong
- picks a category (structural, electrical, safety, finish work, etc)
- rates severity with a reason
- guesses a relevant CSI spec section
- flags when a human should actually confirm it

## run it

```
pip install anthropic
export ANTHROPIC_API_KEY=...
python fieldscan.py your_photo.jpg
```

no key set = prints an example output instead of faking analysis on your photo.

## known issues / limits

- single photo only, no batch mode, no PDF export, no floor plan pinning
- hit a real bug early on: a downloaded image was actually AVIF but named
  .png, script trusted the extension and the API rejected it with a raw
  traceback. fixed by checking the actual file signature (magic bytes)
  instead of the filename
- not tested on a large enough set of real defect photos to know how it
  handles edge cases or ambiguous damage
- this drafts an observation for a human to review, not a replacement for
  an actual inspector's judgment, especially on anything safety related

## if I kept going with this

- batch mode for a whole site visit
- basic web UI instead of CLI
- pin the flagged spot on a floor plan
- export straight to PDF
