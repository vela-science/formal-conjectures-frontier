by
  let e : ℝ ≃ᵢ EuclideanSpace ℝ (Fin 1) :=
    IsometryEquiv.mk'
      (EuclideanSpace.single (0 : Fin 1))
      (fun x => x 0)
      (fun x => by
        ext i
        fin_cases i
        simp)
      (fun x y => by
        simpa using (EuclideanSpace.dist_single_same (0 : Fin 1) x y))
  let T : Set ℝ := e.symm '' S
  have hT : Bornology.IsBounded T :=
    e.symm.isometry.lipschitz.isBounded_image hS
  have hdiam : diam T = diam S := by
    simpa [T] using e.symm.diam_image S
  have hdT : 0 < diam T := hdiam.symm ▸ hd
  let a : ℝ := sInf T
  let b : ℝ := sSup T
  let m : ℝ := (a + b) / 2
  have hab : a ≤ b := by
    exact Real.sInf_le_sSup T hT.bddBelow hT.bddAbove
  have ham : a ≤ m := by
    dsimp [m]
    linarith
  have hmb : m ≤ b := by
    dsimp [m]
    linarith
  let G : Fin 2 → Set ℝ := ![Icc a m, Ioc m b]
  have hcover : T ⊆ ⋃ i, G i := by
    intro x hx
    have hxI : x ∈ Icc a b := hT.subset_Icc_sInf_sSup hx
    by_cases hxm : x ≤ m
    · apply mem_iUnion.2
      refine ⟨0, ?_⟩
      simp [G, hxI.1, hxm]
    · apply mem_iUnion.2
      refine ⟨1, ?_⟩
      have hmx : m < x := lt_of_not_ge hxm
      simp [G, hmx, hxI.2]
  have hG : ∀ i, diam (G i) < diam T := by
    have hdab : 0 < b - a := by
      rw [Real.diam_eq hT] at hdT
      simpa [a, b] using hdT
    intro i
    fin_cases i
    · simp [G]
      rw [Real.diam_Icc ham, Real.diam_eq hT]
      dsimp [m, a, b]
      linarith
    · simp [G]
      rw [Real.diam_Ioc hmb, Real.diam_eq hT]
      dsimp [m, a, b]
      linarith
  refine ⟨fun i => e '' G i, ?_, ?_⟩
  · intro x hx
    have hxT : e.symm x ∈ T := by
      refine ⟨x, hx, ?_⟩
      simp
    rcases mem_iUnion.1 (hcover hxT) with ⟨i, hi⟩
    apply mem_iUnion.2
    exact ⟨i, e.symm x, hi, e.apply_symm_apply x⟩
  · intro i
    rw [e.diam_image]
    exact hdiam ▸ hG i
