# Cross-app work uses durable files

Assign one owner to each transformation; later stages consume the prior result.
The host coordinates normal tool calls. There is no shared in-memory document ID,
transaction, router service, second model, or home-grown queue.

## Photo → layout → PDF

PhotoCraft owns pixel edits and exports a new PNG. Verify dimensions, format and
visual appearance on disk. DesignCraft consumes that exact PNG and owns the page
layout; verify links, story/overset state and its exported PDF. PdfCraft inspects
or audits the PDF when appropriate; it does not repeat the pixel/layout decisions.
Retain paths, hashes and warnings for every intermediate. An audit is not approval.

## Motion → movie (optional audio)

EffectCraft owns the motion composition and exports real media. Verify frame
rate, duration, alpha expectations and a visual frame. FilmCraft imports that
media and owns timeline assembly and final export. Choose either FilmCraft or
SoundCraft as final audio-mix owner, not both. Verify timing, media references,
audio channels/rate and offline-media warnings before final delivery.

## Workbook → presentation

GridCraft is the sole authority for formula calculation and typed cell values.
Export a bounded, verified data artifact and preserve provenance and error values.
DeckCraft consumes that artifact to build the requested slides, then saves and
exports them. Do not ask another model to recalculate the accounting truth.

## Interface design → raster, layout or PDF

FigCraft owns frames, components and prototypes and exports PNG, SVG or PDF
only when `path` is set. Verify dimensions, frame count and the colour profile
on disk (Display P3 converts to sRGB in SVG and PDF). PhotoCraft or VectorCraft
may then own pixel or path edits of that export, DesignCraft the page layout and
PdfCraft the PDF audit; none of them reopens the `.figcraft` document, and an
experimental `.fig` export is not proof of a Figma round trip.

If a stage fails, stop dependent work. Report the last verified file and the
unverified/failed stage. No app can roll back another app's files automatically.
