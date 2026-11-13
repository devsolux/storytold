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

## Procedural material → painted textures

MaterialCraft owns the node graph and exports maps with outputs_export. Verify graph,
cook errors and each map on disk. TextureCraft owns the painted mesh and imports those
maps with resource_import. Hand over only the exported maps: at the pinned pair
TextureCraft cannot load what MaterialCraft writes as a linked material (it reads `.mcmat`
version 1 and the older `.mcraft` layout, MaterialCraft 0.4 writes version 2 and a
`package.sbs` package), so material_load of either fails and a re-cook of an older linked
material fails inside `materialcraft-cli`, which runs outside TextureCraft's roots (see
both cards). Both material_load failures and the exported-map route were observed in the
2026-11-13 acceptance runs: a height map from outputs_export, imported with resource_import
and used as a height layer, reached the saved `.tcraft` byte-identical. Verify the layer,
session_inspect and every exported texture; neither app reopens the other's file.

If a stage fails, stop dependent work. Report the last verified file and the
unverified/failed stage. No app can roll back another app's files automatically.
