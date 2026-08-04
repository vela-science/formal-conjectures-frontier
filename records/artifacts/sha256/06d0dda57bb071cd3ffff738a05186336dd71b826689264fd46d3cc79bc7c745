import Research.Erdos521
import Research.FairPrefix

open Filter MeasureTheory
open scoped Topology

/-!
This file mirrors the definitions in Formal Conjectures PR #4578 at commit
`a3b9c2fef2e5c6dbe1652642c7429abdfbd21c5b`, then proves that its fair-coin
encoding gives the same Claim as the independently compiled proof corpus at
lean-proofs commit `4f915a323443bfb1709a6805a013812016dca88a`.
-/

namespace FormalConjecturesErdos521

def sign (b : Bool) : ℝ := if b then 1 else -1

noncomputable def fairCoin : Measure Bool :=
  (2 : ENNReal)⁻¹ • (Measure.dirac true + Measure.dirac false)

theorem fairCoin_apply (b : Bool) : fairCoin {b} = 2⁻¹ := by
  cases b <;> simp [fairCoin]

theorem fairCoin_eq_proof : fairCoin = Erdos521.fairCoin := by
  apply Measure.ext_of_singleton
  intro b
  rw [fairCoin_apply, Erdos521.fairCoin_singleton]

noncomputable def rademacherMeasure : Measure (ℕ → Bool) :=
  Measure.infinitePi (fun _ : ℕ ↦ fairCoin)

theorem rademacherMeasure_eq_proof :
    rademacherMeasure = Erdos521.rademacherMeasure := by
  rw [rademacherMeasure, Erdos521.rademacherMeasure, fairCoin_eq_proof]

noncomputable def littlewoodPolynomial (ω : ℕ → Bool) (n : ℕ) : Polynomial ℝ :=
  ∑ k ∈ Finset.range (n + 1), Polynomial.monomial k (sign (ω k))

noncomputable def realRootCount (ω : ℕ → Bool) (n : ℕ) : ℕ :=
  Set.ncard ((littlewoodPolynomial ω n).rootSet ℝ)

def Claim : Prop :=
  ∀ᵐ ω ∂rademacherMeasure,
    Tendsto (fun n : ℕ ↦ (realRootCount ω n : ℝ) / Real.log (n : ℝ))
      atTop (𝓝 ((2 : ℝ) / Real.pi))

theorem sign_eq_proof : sign = Erdos521.sign := by
  funext b
  rfl

theorem littlewoodPolynomial_eq_proof :
    littlewoodPolynomial = Erdos521.littlewoodPolynomial := by
  funext ω n
  unfold littlewoodPolynomial Erdos521.littlewoodPolynomial
  rw [sign_eq_proof]

theorem realRootCount_eq_proof : realRootCount = Erdos521.realRootCount := by
  funext ω n
  unfold realRootCount Erdos521.realRootCount
  rw [littlewoodPolynomial_eq_proof]

theorem claim_iff_proof : Claim ↔ Erdos521.Claim := by
  rw [Claim, Erdos521.Claim, rademacherMeasure_eq_proof,
    realRootCount_eq_proof]

theorem negative : ¬ Claim := by
  intro h
  exact Erdos521.erdos_521_negative (claim_iff_proof.mp h)

#print axioms fairCoin_eq_proof
#print axioms claim_iff_proof
#print axioms negative

end FormalConjecturesErdos521
