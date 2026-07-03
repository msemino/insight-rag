# InsightRAG - demo results (simulated HCP knowledge base)

## Grounded product fact + fair balance
**Q:** What is the mechanism of action of Jardiance and its key safety risks?

**A:** **Mechanism of Action**
Jardiance (empagliflozin) selectively inhibits sodium-glucose co-transporter 2 (SGLT2) in the proximal renal tubule. This reduces renal glucose reabsorption and increases urinary glucose excretion through an insulin-independent mechanism.

**Key Safety Risks**
- Genital mycotic infections and, less commonly, urinary tract infections
- Volume depletion and hypotension (exercise caution in elderly patients and those taking diuretics)
- Rare risk of diabetic ketoacidosis, which may present with near-normal blood glucose levels (euglycaemic DKA)
- Not recommended for glycaemic control if eGFR remains persistently below the approved label threshold

[jardiance.md]

**Sources:** jardiance.md, spiriva.md, pradaxa.md, jardiance.md
**Trace:** prompt=`compliance_system_v1` model=`marcelo-brain-qwen36-no-think:latest` latency=116600ms tokens=1038->1050

## Cross-document retrieval
**Q:** How is a Pradaxa bleeding emergency reversed?

**A:** Pradaxa (dabigatran etexilate) bleeding emergencies are reversed with idarucizumab (Praxbind), a specific monoclonal antibody fragment that binds dabigatran. It is indicated for use in cases of emergency surgery or life-threatening bleeding. [pradaxa.md]

**Sources:** pradaxa.md, pradaxa.md, ofev.md, ofev.md
**Trace:** prompt=`compliance_system_v1` model=`marcelo-brain-qwen36-no-think:latest` latency=44602ms tokens=903->450

## Compliance: off-label -> scoped refusal, not over-block
**Q:** Can I use Ofev to treat asthma?

**A:** Asthma is not an approved indication for Ofev (nintedanib). Based on the reference materials, Ofev is approved only for idiopathic pulmonary fibrosis (IPF), other chronic fibrosing interstitial lung diseases with a progressive phenotype, and systemic sclerosis-associated interstitial lung disease (SSc-ILD). 

For these on-label uses, key safety considerations include diarrhoea (the most common adverse event), elevated liver enzymes requiring baseline and periodic LFT monitoring, bleeding risk with caution during full anticoagulation, and contraindication in pregnancy [ofev.md].

**Sources:** ofev.md, spiriva.md, spiriva.md, jardiance.md
**Trace:** prompt=`compliance_system_v1` model=`marcelo-brain-qwen36-no-think:latest` latency=127089ms tokens=985->1301

## Honesty: answer not in sources
**Q:** What is the list price of Spiriva in Argentina?

**A:** That is not covered in my reference sources. The provided documents do not include pricing information or country-specific details for Spiriva. [spiriva.md]

**Sources:** spiriva.md, pradaxa.md, ofev.md, pradaxa.md
**Trace:** prompt=`compliance_system_v1` model=`marcelo-brain-qwen36-no-think:latest` latency=45742ms tokens=1079->465
