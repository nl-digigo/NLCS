"""
merge_searchterms.py
---------------------
Post-processes a per-hoofdgroep split TTL file (Laces-internal OTL schema,
e.g. code/nlcs/split_import_files/GW/merged_all_per_hoofdgroep-5.0-GW.ttl)
to collapse multiple object <-> Arcering/Symbool links into a single
expert-provided "searchterm".

For each Excel row (hoofdgroep, omschrijving, sobject, searchterm):
  - omschrijving   = the NLCS object's otl:attr-Conceptual-name (e.g. "GROND_ZAND")
  - sobject        = "; "-separated list of the existing Arcering/Symbool
                      names currently linked to that object
                      (e.g. "AGW-GROND_ZAND-SO; AGW-GROND_ZAND-SOD")
  - searchterm     = the single new merged name (e.g. "AGW-GROND_ZAND")

For the matched object:
  - the otl:InformationField nodes whose value is one of the sobject terms
    (classified as Arcering or Symbool) are removed from the object's
    otl:rel-Conceptual-isDescribedIn list, and deleted.
  - one new otl:InformationField is added with value = searchterm, same
    info-type classification (Arcering or Symbool).

In the Arcering/Symbool classification tree:
  - the otl:Document nodes whose otl:attr-Conceptual-name matches a sobject
    term are found; they must share one otl:rel-Conceptual-isSpecializationOf
    parent.
  - a new otl:Document node is created for the searchterm, as a
    specialization of that same parent, with the same generic annotation
    InformationFields as its siblings (empty-valued — this is a synthetic
    node with no source record) plus its own Original-URI field.
  - the old otl:Document nodes are re-parented: their
    otl:rel-Conceptual-isSpecializationOf is changed to point at the new
    searchterm node instead of the old parent.

Usage
-----
    python merge_searchterms.py --ttl <input.ttl> --excel <mapping.xlsx> \\
        --hoofdgroep GW --out <output.ttl>
"""

import argparse
import hashlib
import logging
import uuid
from typing import Optional

import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, OWL

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

OTL = Namespace("http://www.laces.tech/publication/ns/semmtech/live/laces/schema/otl-manager/")
SHAPES = Namespace("http://www.laces.tech/publication/ns/semmtech/live/laces/schema/shapes/")

ARCERING_TYPE = URIRef("urn:nlcs:info-type:Arcering")
SYMBOOL_TYPE = URIRef("urn:nlcs:info-type:Symbool")
ORIGINAL_URI_TYPE = URIRef("urn:nlcs:info-type:OriginalURI")

IS_DESCRIBED_IN = OTL["rel-Conceptual-isDescribedIn"]
IS_SPECIALIZATION_OF = OTL["rel-Conceptual-isSpecializationOf"]
IS_CLASSIFIED_AS = OTL["rel-InformationField-isClassifiedAs"]
ATTR_NAME = OTL["attr-Conceptual-name"]
ATTR_FIELD_VALUE = OTL["attr-InformationField-value"]


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def split_sobject(sobject: str) -> list[str]:
    return [s.strip() for s in sobject.split(";") if s.strip()]


def find_object_by_name(g: Graph, name: str) -> Optional[URIRef]:
    matches = [
        s for s in g.subjects(ATTR_NAME, Literal(name))
        if (s, RDF.type, OTL.PhysicalObject) in g
    ]
    if len(matches) > 1:
        log.warning("Multiple PhysicalObject nodes named %r: %s (using first)", name, matches)
    return matches[0] if matches else None


def find_document_by_name(g: Graph, name: str) -> Optional[URIRef]:
    matches = [
        s for s in g.subjects(ATTR_NAME, Literal(name))
        if (s, RDF.type, OTL.Document) in g
    ]
    if len(matches) > 1:
        log.warning("Multiple Document nodes named %r: %s (using first)", name, matches)
    return matches[0] if matches else None


def field_value(g: Graph, field: URIRef) -> Optional[str]:
    for v in g.objects(field, ATTR_FIELD_VALUE):
        return str(v)
    return None


def process_row(
    g: Graph,
    hoofdgroep: str,
    omschrijving: str,
    sobject: str,
    searchterm: str,
    term_index: dict[str, URIRef],
) -> bool:
    terms = split_sobject(sobject)
    if not terms:
        log.warning("[%s] %s: empty sobject, skipping", hoofdgroep, omschrijving)
        return False

    obj_uri = find_object_by_name(g, omschrijving)
    if obj_uri is None:
        log.warning("[%s] Object %r not found — skipping", hoofdgroep, omschrijving)
        return False

    # ── Locate the object's InformationField nodes matching the sobject terms ──
    described_fields = list(g.objects(obj_uri, IS_DESCRIBED_IN))
    matched_fields = []
    info_type: Optional[URIRef] = None
    for f in described_fields:
        val = field_value(g, f)
        if val is None or val not in terms:
            continue
        classified_as = list(g.objects(f, IS_CLASSIFIED_AS))
        if not classified_as:
            continue
        ftype = classified_as[0]
        if ftype not in (ARCERING_TYPE, SYMBOOL_TYPE):
            continue
        matched_fields.append(f)
        if info_type is None:
            info_type = ftype
        elif info_type != ftype:
            log.warning(
                "[%s] %s: sobject terms span both Arcering and Symbool fields — using %s",
                hoofdgroep, omschrijving, info_type,
            )

    found_values = {field_value(g, f) for f in matched_fields}
    missing = set(terms) - found_values
    if missing:
        log.warning("[%s] %s: sobject terms not found as object fields: %s", hoofdgroep, omschrijving, missing)
    if not matched_fields:
        log.warning("[%s] %s: no matching object fields found for %s — skipping object-side merge", hoofdgroep, omschrijving, terms)
    else:
        # Remove old field links + the field nodes themselves.
        for f in matched_fields:
            g.remove((obj_uri, IS_DESCRIBED_IN, f))
            g.remove((f, None, None))

        # Add the single merged field.
        field_prefix = "arc" if info_type == ARCERING_TYPE else "sym"
        new_field = URIRef(f"{obj_uri}-field-{field_prefix}-{sha1(searchterm)}")
        g.add((obj_uri, IS_DESCRIBED_IN, new_field))
        g.add((new_field, RDF.type, OTL.InformationField))
        g.add((new_field, ATTR_FIELD_VALUE, Literal(searchterm)))
        g.add((new_field, IS_CLASSIFIED_AS, info_type))
        log.info("[%s] %s: merged %d field(s) %s -> %r", hoofdgroep, omschrijving, len(matched_fields), sorted(found_values), searchterm)

    # ── Locate the old Document nodes in the classification tree ──
    # A term may already have been absorbed into an earlier (narrower) merge
    # in this same run — term_index redirects to that intermediate node
    # instead of the original leaf, so nested merges compose correctly
    # regardless of how many levels deep they go.
    old_docs = []
    seen_docs = set()
    for term in terms:
        doc = term_index.get(term)
        if doc is None:
            doc = find_document_by_name(g, term)
        if doc is None:
            log.warning("[%s] %s: Document node %r not found in classification tree", hoofdgroep, omschrijving, term)
            continue
        term_index.setdefault(term, doc)
        if doc not in seen_docs:
            seen_docs.add(doc)
            old_docs.append(doc)

    if not old_docs:
        log.warning("[%s] %s: no Document nodes found — skipping tree merge", hoofdgroep, omschrijving)
        return bool(matched_fields)

    # If searchterm names an existing Document (typically one of this row's
    # own old_docs — the expert chose to keep that name as the merge target
    # rather than coin a new one), reuse it instead of fabricating a
    # duplicate-named node, and don't re-parent it under itself.
    existing_new_doc = find_document_by_name(g, searchterm)
    if existing_new_doc is not None:
        new_doc = existing_new_doc
        old_docs = [d for d in old_docs if d != new_doc]
        if not old_docs:
            log.info("[%s] %s: searchterm already is the sole Document node — nothing to re-parent", hoofdgroep, omschrijving)
            for term in terms:
                term_index[term] = new_doc
            return True
        log.info("[%s] %s: reusing existing Document node %s named %r as merge target", hoofdgroep, omschrijving, new_doc, searchterm)
    else:
        parents = {p for d in old_docs for p in g.objects(d, IS_SPECIALIZATION_OF)}
        if len(parents) > 1:
            log.warning("[%s] %s: old Document nodes have differing parents %s — using one arbitrarily", hoofdgroep, omschrijving, parents)
        if not parents:
            log.warning("[%s] %s: old Document nodes have no isSpecializationOf parent — skipping tree merge", hoofdgroep, omschrijving)
            return bool(matched_fields)
        parent = next(iter(parents))

        new_doc = URIRef(f"http://digitalbuildingdata.tech/nlcs/def/{uuid.uuid4()}")
        seq_node = URIRef(f"{new_doc}-seq-name")

        g.add((new_doc, RDF.type, OTL.Document))
        g.add((new_doc, SHAPES["sequence"], seq_node))
        g.add((seq_node, RDF.type, OTL["Seq_attr-Conceptual-name"]))
        g.add((seq_node, RDF["_1"], Literal(searchterm)))
        g.add((seq_node, OWL.annotatedProperty, ATTR_NAME))
        g.add((new_doc, ATTR_NAME, Literal(searchterm)))
        g.add((new_doc, IS_SPECIALIZATION_OF, parent))

        # Reuse the same generic annotation-field "shape" (same SHA1 suffixes
        # + isClassifiedAs type nodes) as the sibling Document nodes, valued
        # empty since this node has no source record.
        template_doc = old_docs[0]
        seen_suffixes = set()
        for f in g.objects(template_doc, IS_DESCRIBED_IN):
            f_str = str(f)
            prefix = str(template_doc)
            if not f_str.startswith(prefix):
                continue
            suffix = f_str[len(prefix):]  # e.g. "-field-<hash>" or "-field-uri"
            if suffix in ("-field-uri",) or suffix.startswith("-field-arc-") or suffix.startswith("-field-sym-"):
                continue  # original-URI / per-object fields — not part of the generic template
            if suffix in seen_suffixes:
                continue
            seen_suffixes.add(suffix)
            classified_as = list(g.objects(f, IS_CLASSIFIED_AS))
            if not classified_as:
                continue
            new_field = URIRef(f"{new_doc}{suffix}")
            g.add((new_doc, IS_DESCRIBED_IN, new_field))
            g.add((new_field, RDF.type, OTL.InformationField))
            g.add((new_field, ATTR_FIELD_VALUE, Literal("")))
            g.add((new_field, IS_CLASSIFIED_AS, classified_as[0]))

        # Original-URI field for the new node itself — present for structural
        # consistency with sibling Document nodes, but left empty since this
        # node is synthetic and has no real pre-split source URI to record.
        uri_field = URIRef(f"{new_doc}-field-uri")
        g.add((new_doc, IS_DESCRIBED_IN, uri_field))
        g.add((uri_field, RDF.type, OTL.InformationField))
        g.add((uri_field, ATTR_FIELD_VALUE, Literal("")))
        g.add((uri_field, IS_CLASSIFIED_AS, ORIGINAL_URI_TYPE))

        log.info("[%s] %s: created new searchterm Document %s (%r) under parent %s", hoofdgroep, omschrijving, new_doc, searchterm, parent)

    # Re-parent the old Document nodes under the new searchterm node.
    for d in old_docs:
        for p in list(g.objects(d, IS_SPECIALIZATION_OF)):
            g.remove((d, IS_SPECIALIZATION_OF, p))
        g.add((d, IS_SPECIALIZATION_OF, new_doc))

    # Redirect every consumed term (and the searchterm itself, in case a
    # broader row later references it directly) to the resulting node, so a
    # later, broader row absorbs this merge node instead of re-touching its
    # now-reparented children.
    for term in terms:
        term_index[term] = new_doc
    term_index[searchterm] = new_doc

    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ttl", required=True, help="Input split TTL file (one hoofdgroep)")
    ap.add_argument("--excel", required=True, nargs="+", help="One or more Excel files with hoofdgroep/omschrijving/sobject/searchterm columns (e.g. one for arcering, one for symbolen)")
    ap.add_argument("--hoofdgroep", required=True, help="Hoofdgroep code to filter Excel rows on (e.g. GW)")
    ap.add_argument("--out", required=True, help="Output TTL file path")
    args = ap.parse_args()

    log.info("Loading TTL %s ...", args.ttl)
    g = Graph()
    g.parse(args.ttl, format="turtle")
    log.info("Loaded %d triples", len(g))

    rows_list = []
    for excel_path in args.excel:
        df = pd.read_excel(excel_path, dtype=str)
        df.columns = [c.strip().lower() for c in df.columns]
        matched = df[df["hoofdgroep"].str.strip() == args.hoofdgroep]
        log.info("%s: %d row(s) for hoofdgroep %s", excel_path, len(matched), args.hoofdgroep)
        rows_list.append(matched)
    rows = pd.concat(rows_list, ignore_index=True) if rows_list else pd.DataFrame()
    if not rows.empty:
        # Process order matters for overlapping/nested rows: a row whose
        # searchterm literally reuses one of its own sobject terms is always
        # the innermost layer (it attaches to an existing leaf, changing
        # nothing about that leaf's own parent) and must run before any row
        # that later absorbs the same terms into a genuinely new, broader
        # node — otherwise the broader node can end up wrapped *inside* the
        # very node it was supposed to be the parent of, producing a
        # isSpecializationOf cycle. Term count alone isn't a reliable
        # tie-breaker: two overlapping rows can have equal term counts when
        # a "family" has only one sub-variant instead of several.
        rows = rows.assign(
            _term_count=rows["sobject"].apply(lambda s: len(split_sobject(s))),
            _is_reuse=rows.apply(lambda r: r["searchterm"].strip() in split_sobject(r["sobject"]), axis=1),
        )
        rows = rows.sort_values(["_is_reuse", "_term_count"], ascending=[False, True], kind="stable")
    log.info("Processing %d row(s) total for hoofdgroep %s", len(rows), args.hoofdgroep)

    term_index: dict[str, URIRef] = {}
    changed = 0
    for _, row in rows.iterrows():
        ok = process_row(g, args.hoofdgroep, row["omschrijving"].strip(), row["sobject"], row["searchterm"].strip(), term_index)
        changed += int(ok)

    log.info("Applied %d/%d row(s)", changed, len(rows))

    cycle = find_specialization_cycle(g)
    if cycle is not None:
        raise SystemExit(
            f"Aborting: otl:rel-Conceptual-isSpecializationOf cycle detected involving {cycle} "
            "— refusing to write a broken output file."
        )

    log.info("Serializing to %s ...", args.out)
    g.serialize(destination=args.out, format="turtle")
    log.info("Done. %d triples in output.", len(g))


def find_specialization_cycle(g: Graph) -> Optional[list]:
    """Detect any cycle in the otl:rel-Conceptual-isSpecializationOf graph.

    Returns the cycle as a list of nodes if one exists, else None. A safety
    net so a bug in the merge/reparenting logic is caught here instead of
    surfacing later as a Laces import failure.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict = {}

    def visit(node, path):
        color[node] = GRAY
        path.append(node)
        for parent in g.objects(node, IS_SPECIALIZATION_OF):
            state = color.get(parent, WHITE)
            if state == GRAY:
                cycle_start = path.index(parent)
                return path[cycle_start:] + [parent]
            if state == WHITE:
                result = visit(parent, path)
                if result is not None:
                    return result
        path.pop()
        color[node] = BLACK
        return None

    for doc in set(g.subjects(RDF.type, OTL.Document)):
        if color.get(doc, WHITE) == WHITE:
            result = visit(doc, [])
            if result is not None:
                return result
    return None


if __name__ == "__main__":
    main()
