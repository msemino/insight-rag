# Semantic layer — ontology, reasoning, governance

The knowledge graph in `app/graph/` is a property graph: strings joined by string
relations. It works, and it hits a ceiling fast. This layer is the schema those
triples conform to, plus a reasoner and a validator.

The distinction that matters: **a knowledge graph is data, an ontology is the
contract that data is held to.** Managing ontologies means owning the vocabulary,
the rules that derive facts from it, and the checks that fail the build when the
data drifts away from it.

## What it buys, measured

| | flat KG | + semantic layer |
|---|---|---|
| Question "which product for COPD?" | links nothing | `Aerivo` |
| Question "any anticoagulant?" | links nothing | `Vestrila` (only typed as a DOAC) |
| Question "what does Norwick offer for T2D?" | links nothing | `Orvenda` |
| "Which products have **no** reversal agent?" | not answerable | exact, 3 rows |
| Orvenda's authorisation holder | `"Norwick Pharma / Halvern Biosciences alliance"` (a string) | resolves to both member companies |
| Data-quality check | none | 3 SHACL shapes in CI |

`compare_linking.py` recovers **6 of 7** realistic HCP questions that the
substring linker drops entirely. The seventh is the control — a brand name, which
substring matching already handles.

## Files

| File | What it is |
|---|---|
| `ontology.ttl` | The TBox: classes, object properties with inverses, two OWL 2 RL property chains, the drug-class taxonomy, and every synonym. |
| `build.py` | Lifts `app/graph/kg.json` into RDF individuals under the schema. Keeps `sourceDocument`, so citations survive. → `kg.ttl` |
| `reason.py` | OWL 2 RL closure (owlrl), then diffs against the asserted graph and prints exactly which facts were derived. → `kg-inferred.ttl` |
| `shapes.ttl` / `validate.py` | SHACL contract, run twice — asserted vs inferred — so the reasoner's contribution is visible rather than claimed. |
| `link.py` | Entity linking over `prefLabel` + `altLabel`, then a hop to the products. Reports which label matched. |
| `compare_linking.py` | A/B against the incumbent substring linker. |
| `sparql.py` | Five named queries: identity, taxonomy, negation, aggregation, multi-hop profile. |

## Run it

```bash
python app/onto/build.py            # lift the KG into RDF
python app/onto/reason.py           # derive + report new facts
python app/onto/validate.py         # SHACL, before and after reasoning
python app/onto/compare_linking.py  # A/B vs substring linking
python app/onto/sparql.py           # the queries dense retrieval answers badly
python tests/test_onto.py           # 8 offline tests, also in CI
```

## The two rules that do the work

```turtle
ins:madeBy       owl:propertyChainAxiom ( ins:madeBy ins:hasMember ) .
ins:hasDrugClass owl:propertyChainAxiom ( ins:hasDrugClass skos:broaderTransitive ) .
```

The first is identity resolution: a product marketed by an alliance is marketed by
each member. The second is taxonomic subsumption: a DOAC is an anticoagulant is an
antithrombotic agent, and a question about any of the three reaches the product.

Neither rule is code. They are declarations, versioned in a `.ttl` file, and the
reasoner applies them — which is the whole argument for a semantic layer over
hand-written traversal logic.

## Two defects this layer found in its own data

Both are recorded because they are the honest reason the tests exist.

1. **The taxonomy chain was inert.** `skos:broader` only feeds
   `skos:broaderTransitive` if the SKOS axioms are in the graph, and they were not.
   The rule fired zero times and nothing failed — `reason.py`'s diff report is what
   surfaced it. Fixed by asserting the two axioms locally.
2. **Every organization had two preferred labels.** The TBox wrote plain literals,
   `build.py` wrote `@en` ones; equal as strings, distinct as RDF terms. Symptom was
   duplicated SPARQL rows, not an error. `ins:LabelShape` now fails CI on it.

## What this is not

- **No mapping to real reference vocabularies.** Production pharma work binds these
  concepts to SNOMED CT, MedDRA, RxNorm and IDMP instead of minting local URIs. The
  URI scheme here is deliberately local and the vocabulary is 31 individuals.
- **Not stored in a graph database.** The graph lives in memory via rdflib and is
  rebuilt per process. Neo4j or a triple store with a SPARQL endpoint is the next
  step; the schema is designed for it but has not been run there.
- **The ontology itself is not versioned beyond `owl:versionInfo "onto_v1"`.** No
  deprecation policy, no change log, no review workflow — which is most of what
  ontology *management* means once more than one person edits it.
- **Synonyms are hand-written.** Mining them from query logs, or importing them
  from a reference vocabulary, is what makes coverage real rather than anecdotal.
