# Presentation Defense Script: PKI-Based Trust Management Case Study

**Candidate:** Shreyan Nayak (Reg. No: `23BKT0039`)  
**Department:** School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Chennai  
**Course Code:** `VL2026270102689` | **Assessment Task:** Case Study 1 (`CS1`)  
**Presentation Title:** PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms  
**Technical Baseline:** `v9.0-FINAL-FREEZE` (October 9, 2026)  
**Target Slide Count:** Exactly 15 Slides | **Estimated Oral Duration:** 15–18 Minutes  

---

## Speaker Delivery Guide & Defense Strategy

1. **Pacing & Timing:** Allocate approximately 1 minute per slide (Slides 8, 12, and 13 may take 1.5 minutes; Slides 1 and 15 require ~30–45 seconds).
2. **Scientific Candor:** Emphasize the refutation of Hypothesis H-1 and the Scenario 7 degeneracy directly. Evaluators respect methodological rigor over inflated claims.
3. **Clear Distinctions:** Rigorously preserve the boundary between the *implemented and evaluated P2P file sharing* protocol (1,140 trials) and the *conceptual-only social-networking extension*.
4. **Mathematical Precision:** State the exact formula $T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$ and its three assumptions (closure, zero coalition teleportation, no dangling rows) when discussing Slide 13.

---

## Slide 1: Title and Candidate Details

### Spoken Explanation (Medium Length)
Good morning, respected evaluators and members of the review committee. My name is Shreyan Nayak, registration number 23BKT0039, from the School of Computer Science and Engineering at VIT Chennai. Today, I am defending my final research case study titled: 'PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms.'

In traditional client-server environments, trust is treated as an externalized administrative assumption: we rely on centralized Certificate Authorities like DigiCert or Let's Encrypt. However, open decentralized networks cannot adopt centralized roots without reintroducing single points of failure and censorship risks. This project presents a vertically integrated four-layer architecture that synthesizes self-sovereign identity, mesh Web-of-Trust PKI, evidence-weighted spectral reputation, and threshold key recovery. Over the next 15 minutes, I will walk you through the protocol design, our preregistered empirical findings across 1,140 simulation runs, and a candid critical analysis of both our successes and our theoretical boundaries.

### Verbal Transition to Next Slide
> *"To understand why this architecture is necessary, let us examine the fundamental dilemma of trust in decentralized networks."*

### Evaluator Q&A Technical Definitions
- **Self-Sovereign Identity (SSI):** An identity model where entities own and control their identifiers and key material without relying on an administrative authority or centralized identity provider.
- **Spectral Reputation:** Reputation algorithms, like PageRank or EigenTrust, that compute global trust scores by finding the principal eigenvector of a normalized stochastic interaction matrix.
- **Freeze Baseline (v9.0-FINAL-FREEZE):** The frozen technical state of the research codebase where specifications, experimental parameters, and mathematical proofs are strictly locked against retroactive tuning.

---

## Slide 2: Introduction and Background

### Spoken Explanation (Medium Length)
Decentralized networks operate under a severe security dilemma. In client-server architectures, X.509 Certificate Authorities anchor trust hierarchically. But if a P2P file-sharing network or decentralized social graph adopts a central CA, that CA becomes a single point of failure and an engine of censorship. Conversely, if we eliminate identity infrastructure entirely, the network becomes defenseless against zero-cost Sybil swarms, strategic collusion rings, receipt grinding, and data poisoning.

We examine this challenge across two distinct distributed paradigms. The first is transactional P2P file sharing, exemplified by BitTorrent and IPFS, where peers exchange immutable binary chunks and trust is verifiable through cryptographic hash manifests. The second is relational decentralized social networking, such as Nostr or Matrix, where interactions consist of subjective follows, message attestations, and moderation.

I want to highlight a vital scope boundary upfront: our file-sharing architecture was fully implemented in Python and empirically validated across 1,140 benchmark trials; our social networking extension is formulated as a formal architectural conceptual mapping, not an empirically validated deployment.

### Verbal Transition to Next Slide
> *"Having outlined the operational environment, let us formalize the exact problem statement and research objectives."*

### Evaluator Q&A Technical Definitions
- **Sybil Attack:** An attack where a single adversary creates a massive number of pseudonymous identities to gain disproportionate influence over a peer-to-peer voting or reputation mechanism.
- **Receipt Grinding:** An adversarial strategy where colluding nodes manufacture high volumes of synthetic, zero-cost transactions among themselves to artificially harvest global reputation.
- **Scope Boundary:** The rigorous methodological separation between software components validated by empirical benchmark data versus extensions established conceptually.

---

## Slide 3: Problem Statement and Research Objectives

### Spoken Explanation (Medium Length)
Our core research problem asks: 'How can autonomous peers establish cryptographically verifiable identity and compute robust global reputation in the absence of centralized Certificate Authorities, while bounding Sybil injection and resisting strategic collusion cliques?'

To solve this problem systematically, we established four formal research objectives:
Under Research Objective 1, we design an identity and admission mechanism that binds Ed25519 public keys to deterministic DIDs and enforces a non-interactive Proof-of-Work challenge to impose computational friction on Sybil identity creation.
Under Research Objective 2, we implement a decentralized Web-of-Trust mesh PKI where peers issue lightweight peer certificates and validate trust paths within a bounded depth horizon of 3 hops.
Under Research Objective 3, we develop Evidence-Weighted EigenTrust v1.8, replacing subjective peer ratings with cryptographic bilateral receipts and severe dispute penalties.
Under Research Objective 4, we formulate Merkle tree chunk fault attribution to pinpoint poisoned data and implement Shamir threshold cryptography for distributed master key recovery.

### Verbal Transition to Next Slide
> *"To situate these four objectives within the existing state of the art, let us review the relevant literature and identify the research gap."*

### Evaluator Q&A Technical Definitions
- **Bounded Breadth-First Search (BFS):** A graph search algorithm restricted to a maximum depth (here, d <= 3) to prevent combinatorial explosion and exponential transitive trust decay.
- **Non-Interactive Proof-of-Work:** A cryptographic puzzle where a prover generates a valid nonce without interacting with a verifier, allowing any third party to verify the proof in O(1) time.
- **Merkle Fault Attribution:** Using cryptographic inclusion paths to deterministically prove that a specific transmitted data block contradicts the authenticated root hash published in a manifest.

---

## Slide 4: Literature Review and Research Gap

### Spoken Explanation (Medium Length)
Our investigation builds upon three major pillars in decentralized security literature.

First, classical Web-of-Trust schemes, originating with Phil Zimmermann's PGP in 1995 and formal SPKI RFC 2693, pioneered decentralized key certification. However, PGP relies on manual, subjective signing and suffers from catastrophic confidence decay over multi-hop paths. Crucially, PGP provides no mathematical algorithm for computing global network-wide reputation.

Second, spectral reputation systems, most notably Kamvar, Schlosser, and Garcia-Molina's seminal 2003 EigenTrust algorithm, introduced global trust computation via Markov chain power iteration. Yet classical EigenTrust assumes a permanently honest set of pre-trusted bootstrap nodes and treats all reported ratings equally, leaving it vulnerable to unconstrained receipt grinding and coordinated rating rings.

Third, Decentralized Identifiers from the W3C and Proof-of-Work from Satoshi Nakamoto provide self-sovereign naming and Sybil rate-limiting, but they deliberately decouple identity from operational accountability.

The critical research gap is this separation: existing PKI systems authenticate cryptographic keys without assessing behavioral integrity, while reputation algorithms evaluate behavior over malleable pseudonyms. Our contribution is the vertical integration of both paradigms into a cohesive four-layer architecture.

### Verbal Transition to Next Slide
> *"Let us examine how this vertical integration is structured across our four architectural layers."*

### Evaluator Q&A Technical Definitions
- **EigenTrust (Kamvar 2003):** A canonical P2P reputation algorithm computing global trust as the stationary distribution of a random walk with restart over normalized local peer ratings.
- **SPKI (Simple Public Key Infrastructure):** IETF RFC 2693 standard focusing on authorization and decentralized key binding rather than identity hierarchies.
- **Decoupled Identity Gap:** The architectural flaw where identity generation and reputation accounting operate in isolation, allowing discredited peers to easily whitewash their history.

---

## Slide 5: Proposed Four-Layer Architecture

### Spoken Explanation (Medium Length)
Slide 5 presents the structural blueprint of our four-layer architecture. We enforce a strict unidirectional dependency invariant: higher layers consume cryptographically authenticated primitives produced by lower layers, guaranteeing that reputation is never computed over unauthenticated entities.

At Layer 1, the Identity and Admission layer binds Ed25519 keypairs to deterministic DIDs and requires solving a SHA-256 Proof-of-Work challenge to throttle Sybil generation.

At Layer 2, the Web-of-Trust Mesh PKI manages peer-to-peer certificates, enforcing a 30-day temporal validity window and bounded transitive trust traversal up to depth 3.

At Layer 3, Evidence-Weighted EigenTrust v1.8 computes spectral reputation. It replaces scalar ratings with bilateral delivery receipts, penalizes Merkle disputes at 5 times positive weight, and executes damped power iteration.

At Layer 4, the Revocation and Key Governance layer executes epidemic gossip CRL dissemination for convicted nodes and provides Shamir (3, 5) polynomial secret sharing for distributed master key recovery.

This vertical synthesis ensures that every interaction processed by the trust engine is cryptographically grounded.

### Verbal Transition to Next Slide
> *"Let us now drill down into each layer in detail, beginning with Layer 1 identity and admission."*

### Evaluator Q&A Technical Definitions
- **Unidirectional Dependency:** An architectural principle ensuring that upper layers depend strictly on lower layers, preventing circular dependencies and state corruption.
- **Layered Defense-in-Depth:** A security paradigm where multiple independent layers of defense cooperate so that the failure of one layer does not compromise the entire system.
- **Deterministic Binding:** An immutable algorithmic mapping where an identity string is uniquely and reproducibly derived from underlying cryptographic material.

---

## Slide 6: Layer 1 — Identity and Proof-of-Work Admission

### Spoken Explanation (Medium Length)
Layer 1 establishes the cryptographic foundation of the network. We define a self-sovereign DID method string: `did:pki:ed25519:` followed by the 64-character hexadecimal public key. Because the public key is embedded directly into the DID URI, identity spoofing is cryptographically impossible: an entity cannot assert an identity without demonstrating possession of the corresponding Ed25519 private key during the mutual handshake.

To mitigate zero-cost Sybil attacks, identity creation requires solving a non-interactive Proof-of-Work challenge: the peer must find a nonce N such that SHA-256 of the DID concatenated with N yields D leading zero bits. At our baseline difficulty of D=16 bits, finding a solution requires an average of 65,536 hash operations, taking approximately 15 to 50 milliseconds on commodity hardware.

The verification is completely asymmetric: while generating the proof requires O(2^D) brute-force hashing, verifying peers validate the proof in O(1) constant time with a single SHA-256 hash evaluation.

However, under our rigorous audit standards, we must qualify this result: Proof-of-Work is an economic rate limiter, not a permanent mathematical barrier against Sybils. An adversary with dedicated GPU or ASIC clusters can overcome static difficulty barriers.

### Verbal Transition to Next Slide
> *"Once identities are admitted through Layer 1, how do peers certify each other's keys? This brings us to Layer 2."*

### Evaluator Q&A Technical Definitions
- **Ed25519:** An elliptic curve digital signature scheme using Curve25519 and SHA-512, offering 128-bit security, high performance, and resistance to side-channel attacks.
- **Proof-of-Work Asymmetry:** A computational property where generating a proof is computationally expensive (O(2^D)), but verifying it is trivial and constant-time (O(1)).
- **Economic Throttling vs. Absolute Defense:** The distinction between mechanisms that make attacks financially or computationally expensive versus cryptographic proofs that make attacks mathematically impossible.

---

## Slide 7: Layer 2 — Web-of-Trust Mesh PKI

### Spoken Explanation (Medium Length)
Layer 2 implements our decentralized Web-of-Trust mesh PKI. Instead of hierarchical X.509 CAs, peers issue and exchange lightweight `PeerCertificate` structures containing the issuer DID, subject DID, subject public key, a strict 30-day temporal validity window, and an Ed25519 digital signature.

When a peer encounters an unfamiliar node, it verifies key authenticity by executing a bounded Breadth-First Search over its local trust graph. To prevent path explosion and transitive dilution, traversal is capped at a maximum depth of 3 hops. Path confidence decays exponentially as delta to the power of k, where delta is 0.5 per hop.

Before accepting any certificate along the path, the verifier cross-checks its local Certificate Revocation List (CRL) to ensure that none of the intermediate issuers have been revoked.

We emphasize an essential conceptual boundary: a valid Layer 2 certificate confirms public key binding authenticity—that is, that the public key legitimately belongs to that peer. It does not certify that the peer is operationally reliable. Behavioral honesty is evaluated separately at Layer 3.

### Verbal Transition to Next Slide
> *"With authenticated identities and certified public keys established, let us examine how Layer 3 computes spectral reputation."*

### Evaluator Q&A Technical Definitions
- **PeerCertificate:** A lightweight, decentralized credential signed by an individual peer asserting the authenticity of another peer's public key.
- **Transitive Trust Decay:** The mathematical reduction in confidence as an endorsement is relayed across intermediate hops (Conf = delta^k).
- **Key Authenticity vs. Behavioral Honesty:** The fundamental distinction between verifying that a key belongs to a peer (PKI) versus verifying that the peer acts honestly (reputation).

---

## Slide 8: Layer 3 — Evidence-Weighted EigenTrust v1.8

### Spoken Explanation (Medium Length)
Layer 3 contains our reputation algorithm: Evidence-Weighted EigenTrust v1.8. In classical EigenTrust, raw ratings are arbitrary integers submitted subjectively by peers. In EW-EigenTrust, raw scores S_ij are derived strictly from cryptographically authenticated evidence.

The formula is: S_ij equals max of 0 and w_pos times positive receipts, minus w_dispute times substantiated disputes, minus w_neg times delivery failures. We configure w_pos to 1.0, w_neg to 2.0, and w_dispute to 5.0. This 5-to-1 asymmetric penalty means that a single proved Merkle corruption wipes out the reputation earned from five successful transactions.

Scores are row-normalized to produce stochastic transition matrix C'. If a peer has zero interactions, its row falls back to the pre-trusted restart distribution p. Global trust vector t is then computed via damped power iteration: t^(k+1) equals (1 - alpha) times C'^T times t^(k) plus alpha times p, with damping factor alpha set to 0.15.

By the Perron-Frobenius theorem, this damped formulation guarantees that the power iteration converges to a unique, strictly positive stationary distribution in approximately 12 to 25 iterations.

### Verbal Transition to Next Slide
> *"What happens when a peer behaves maliciously or a private key is lost? This brings us to Layer 4 revocation and key recovery."*

### Evaluator Q&A Technical Definitions
- **Perron-Frobenius Theorem:** A fundamental mathematical theorem stating that any irreducible, aperiodic stochastic matrix possesses a unique, positive principal eigenvector with eigenvalue 1.
- **Damping Factor (alpha = 0.15):** The probability of teleporting back to the pre-trusted seed distribution p, ensuring the Markov chain is ergodic and cannot be trapped in absorbing cliques.
- **Asymmetric Dispute Weighting:** A penalty calibration where negative evidence (disputes) is penalized far more heavily than positive evidence, preventing hit-and-run reputation harvesting.

---

## Slide 9: Layer 4 — Revocation and Key Recovery

### Spoken Explanation (Medium Length)
Layer 4 addresses two critical lifecycle challenges in decentralized PKI: certificate revocation and key recovery.

In centralized systems, revocation relies on OCSP responders or central CRL distributions, which fail under network partitions. In our design, revocations are triggered either voluntarily when a key is compromised, or involuntarily when a peer is convicted by an undeniable Merkle dispute proof. Revocation messages are signed and propagated across the P2P overlay via epidemic gossip. Once cached in a peer's local CRL, all incoming and outgoing trust edges for the revoked node are instantly severed.

For key recovery, we implement Shamir's (k, n) threshold secret sharing scheme with threshold k=3 out of n=5 guardians. The master private key is embedded as the constant term of a degree-2 random polynomial over Galois Field GF(2^8). Any 3 guardians can cooperate via Lagrange polynomial interpolation to reconstruct the private key, whereas 2 or fewer colluding guardians gain mathematically zero information about the secret.

We clearly report that while Shamir sharing is fully implemented and tested at the cryptographic unit level, live multi-party network recovery was not simulated in the benchmark trials.

### Verbal Transition to Next Slide
> *"Let us now examine how all four layers operate together during an end-to-end file-sharing transaction."*

### Evaluator Q&A Technical Definitions
- **Epidemic Gossip Protocol:** A decentralized message dissemination method where peers periodically forward information to random neighbors, achieving exponential broadcast without a central coordinator.
- **Shamir (k, n) Secret Sharing:** An information-theoretically secure threshold scheme where a secret is divided into n shares, requiring any k shares to reconstruct it, while k-1 shares reveal zero information.
- **Galois Field GF(2^8):** A finite field with 256 elements, commonly used in cryptography to perform byte-level polynomial arithmetic without numerical overflow.

---

## Slide 10: End-to-End File-Sharing Workflow and Merkle Fault Attribution

### Spoken Explanation (Medium Length)
Slide 10 details our end-to-end file sharing protocol and Merkle fault attribution mechanism.

The workflow follows five discrete stages: First, mutual TLS handshake with Ed25519 challenge nonces. Second, Web-of-Trust path verification up to depth 3. Third, file manifest exchange containing the Merkle root hash R. Fourth, chunk delivery along with its Merkle audit path. Fifth, evidence settlement.

I want to focus on our Merkle fault attribution complexity. For a file divided into N chunks, proof verification requires exactly O(log N) hash operations and O(log N) sibling hashes. This logarithmic complexity allows a downloader to verify chunk integrity immediately without downloading the full file. If the calculated root differs from the manifest root, the downloader generates a contradiction proof that indisputably convicts the uploader of data poisoning while preventing malicious downloaders from filing false slander complaints.

We also document our Tier 3 Evidence Portability Gap: in the simulation, delivery receipts rely on a global simulator key oracle. In a live decentralized deployment, bilateral receipts are signed pairwise and require threshold attestation to achieve full third-party portability.

### Verbal Transition to Next Slide
> *"Now that we have established the full theoretical and protocol pipeline, let us review our experimental benchmark setup."*

### Evaluator Q&A Technical Definitions
- **Merkle Inclusion Proof:** A cryptographic path of sibling hashes of length O(log N) that proves a specific chunk belongs to a Merkle tree with root R without downloading the entire tree.
- **Contradiction Proof:** A verifiable cryptographic proof demonstrating that a received chunk hashes to a value conflicting with a previously signed commitment.
- **Tier 3 Evidence Portability Gap:** The architectural limitation where bilateral receipts signed between two peers cannot be trustlessly verified by arbitrary third parties without an external key oracle or threshold consensus.

---

## Slide 11: Experimental Methodology and Benchmark Setup

### Spoken Explanation (Medium Length)
Our experimental evaluation was executed under a strict preregistered protocol—Phase 8.2—encompassing 1,140 total simulation trials. To ensure reproducibility and eliminate random seed bias, we implemented a paired simulation design: exactly 100 identical random seeds were evaluated across all three trust computation modes.

We evaluated networks of 30 and 50 nodes, configured with 20 honest peers, 5 strategic colluders, and 5 malicious Sybil nodes. We tested three operational modes: Standard EigenTrust as the baseline, Evidence-Weighted EigenTrust v1.8, and PoW-Gated EW-EigenTrust.

Our benchmark tested eight distinct threat scenarios across three clusters:
Cluster 1 evaluated identity flooding, whitewashing, and transaction spam.
Cluster 2 evaluated collusion topologies, comparing closed collusion rings where colluders only interact internally against leaky coalitions where colluders also trade with honest nodes.
Cluster 3 evaluated dynamic exploitation, including receipt grinding, slander attacks, and dynamic peer churn.

All statistical comparisons were evaluated using paired two-sided Wilcoxon signed-rank tests and Cohen's d effect sizes.

### Verbal Transition to Next Slide
> *"Let us examine the empirical findings generated from these 1,140 benchmark trials."*

### Evaluator Q&A Technical Definitions
- **Paired Simulation Design:** A rigorous experimental methodology where identical pseudo-random seeds and interaction sequences are executed across different algorithmic treatments to isolate treatment effects.
- **Wilcoxon Signed-Rank Test:** A non-parametric statistical hypothesis test used to compare two paired treatments, making no assumptions about normal distribution.
- **Cohen's d Effect Size:** A standardized measure of the magnitude of difference between two groups; values above 0.8 represent large effects (our leaky collusion suppression achieved d = 2.45).

---

## Slide 12: Key Empirical Results and Statistical Findings

### Spoken Explanation (Medium Length)
Slide 12 summarizes our primary empirical results. The benchmark reveals both decisive successes and critical negative findings.

Our headline validated result occurs in Scenario 5—the leaky coalition scenario. Under Standard EigenTrust, colluders accumulated 18.34% of global network trust. Under EW-EigenTrust, their trust dropped to 10.68%—a 41.8% suppression with extreme statistical significance (p < 10^-6, Cohen's d = 2.45). When colluders interact with honest nodes and fail protocol checks, dispute weighting severely restricts incoming trust flow.

However, in Scenario 6—receipt grinding—colluders actually increased their trust share: gaining +13.38% under standard grinding and +17.92% under extended grinding. This directly refuted our preregistered Hypothesis H-1.

In Scenario 7, colluder trust was reported as 0.0000; as I will explain on the next slide, this was a structural artifact.

Finally, regarding runtime overhead: under normal conditions, matrix assembly takes 34.2 ms compared to 28.4 ms for EigenTrust—only a 20% overhead. But under extended grinding with 152,000 receipts, runtime surged to 2.76 seconds—a 92-fold overhead that demonstrates significant memory and computational scaling bottlenecks under unpruned history.

### Verbal Transition to Next Slide
> *"To interpret these empirical results scientifically, let us dive into our critical theoretical analysis on Slide 13."*

### Evaluator Q&A Technical Definitions
- **Leaky Coalition:** A collusion ring where malicious members interact with honest nodes to siphon legitimate trust before channeling it to confederates.
- **Trust Share:** The fraction of total network trust mass (which sums to 1.0) captured by a specific subgroup of nodes.
- **Runtime Scaling Overhead:** The computational and memory degradation resulting from processing quadratic transaction volumes without state pruning (92x overhead under 152k receipts).

---

## Slide 13: Critical Analysis: Closed-Set Flow Identity, H-1 Refutation, & Scenario 7 Degeneracy

### Spoken Explanation (Medium Length)
Slide 13 provides the critical analysis that distinguishes rigorous science from superficial claims.

First, we examine the Closed-Set Flow Identity: T_C equals (1 - alpha) divided by alpha times F_(H -> C). This theorem proves that the total trust mass captured by any closed coalition C depends strictly on the trust-weighted flow entering from honest nodes. It rests on three precise assumptions: coalition closure (C'_ch = 0), zero coalition teleportation (p_c = 0), and no dangling coalition rows. Crucially, total coalition trust is invariant to internal reputation grinding if and only if the incoming flow F_(H -> C) remains constant.

Second, we address the refutation of Hypothesis H-1. We originally hypothesized that dispute weighting would suppress colluder trust during receipt grinding. In reality, colluders gained 13% to 18% more trust. Why? Because colluders manufactured synthetic positive receipts entirely among themselves without interacting with honest nodes or triggering disputes. Because no disputes occurred, dispute weighting was never activated.

Third, we explain the Scenario 7 zero-trust result. Reporting 0.0000 colluder trust looked like perfect defense. However, inspection revealed it was structurally degenerate: colluders had zero incoming flow (F_(H -> C) = 0), zero teleportation mass (p_c = 0), and no dangling rows. Their trust was zero due to topological disconnection, not adaptive dispute mitigation.

### Verbal Transition to Next Slide
> *"With these theoretical boundaries established, let us review our limitations, social networking scope, and conclusions."*

### Evaluator Q&A Technical Definitions
- **Closed-Set Flow Identity:** The mathematical theorem proving that total trust mass of a closed coalition C is strictly governed by T_C = ((1 - alpha)/alpha) * F_(H -> C).
- **Topological Disconnection:** A network graph state where no directed edges exist from the honest component to the colluding subgraph, forcing incoming flow F_(H -> C) to zero.
- **Scientific Refutation (H-1):** The candid empirical falsification of a preregistered hypothesis, demonstrating academic integrity over selective reporting.

---

## Slide 14: Limitations, Social-Networking Scope & Conclusion

### Spoken Explanation (Medium Length)
In concluding our defense, we review our project limitations, define our social-networking scope, and outline future directions.

We candidly acknowledge three architectural limitations: first, the Tier 3 evidence portability gap; second, the fact that static Proof-of-Work provides economic friction rather than absolute Sybil defense against ASIC adversaries; and third, that our 1,140 trials were conducted in discrete-event simulation rather than live WAN deployments.

Regarding decentralized social networks: we formulated a platform-neutral conceptual mapping linking Nostr follows to WoT trust edges, signed post attestations to bilateral receipts, and social recovery to Shamir guardian sets. However, because social trust is inherently subjective and lacks binary Merkle corruption proofs, we strictly delineate this as an architectural conceptual extension, without claiming empirical validation.

In conclusion, our research demonstrates that a vertically integrated PKI architecture achieves over 40% leaky collusion suppression while formally defining the mathematical limits of spectral reputation. Future research will explore zero-knowledge receipt compression to eliminate the 92x runtime scaling bottleneck and decentralized multi-party threshold consensus.

### Verbal Transition to Next Slide
> *"Finally, Slide 15 lists the foundational literature supporting our work."*

### Evaluator Q&A Technical Definitions
- **Zero-Knowledge Receipt Compression:** Using cryptographic zk-SNARKs or recursive proofs to compress thousands of transaction receipts into a single constant-size proof, eliminating runtime scaling bottlenecks.
- **Subjective vs. Objective Trust:** The distinction between verifiable binary assertions (e.g., Merkle chunk hash matches) versus subjective interpersonal preferences (e.g., social follows).
- **Multi-Party Threshold Consensus:** A distributed protocol where nodes reach consensus on key recovery or certificate issuance without relying on any single trusted node.

---

## Slide 15: Authoritative Academic References

### Spoken Explanation (Medium Length)
Slide 15 presents our complete bibliography, formatted according to IEEE standards.

These seven authoritative references represent the core theoretical foundations of our project: the W3C DID standard [1] for Layer 1; SPKI RFC 2693 [2], Zimmermann's PGP [6], and RFC 5280 [7] for Layer 2 mesh PKI and revocation; Kamvar et al.'s EigenTrust [3] for Layer 3 spectral iteration; Satoshi Nakamoto's Bitcoin [4] for Proof-of-Work admission; and Adi Shamir's 1979 ACM paper [5] for threshold secret sharing.

All empirical numbers, formulas, and baseline parameters in this defense have been verified against these foundational works and our frozen research baseline.

Thank you very much for your time and consideration. I am now prepared to answer questions from the evaluation committee.

### Verbal Transition to Next Slide
> *"Conclusion of presentation. Open floor for committee questions and defense discussion."*

### Evaluator Q&A Technical Definitions
- **IEEE Reference Format:** The standard citation style used in IEEE engineering publications, utilizing numbered citations [1]-[7] aligned with bibliography entries.
- **Foundational Baseline:** The established peer-reviewed literature upon which the case study's theoretical claims and security assumptions are anchored.
- **Oral Defense Protocols:** The standard academic examination procedure evaluating candidate mastery of theory, implementation rigor, statistical analysis, and limitations.

---
