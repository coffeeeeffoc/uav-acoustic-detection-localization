# Acoustic Detection and Direction Finding of Small UAVs Using Direction Conditioned Coherence Ranking

## Abstract

Acoustic direction finding can localize a coherent background source even when an unmanned aerial vehicle (UAV) is audible. A detection decision applied after selecting the strongest spatial peak does not resolve this source-association error. This paper presents direction-conditioned coherence ranking (DCCR), which generates four bearing hypotheses with steered response power and the phase transform (SRP-PHAT), then ranks them using a learned 24-band directional coherence signature. A class-balanced ridge model is trained with both background recordings and incorrect directions from aircraft recordings. The representation excludes absolute signal level and direction coordinates. Experiments use a 208-channel planar array and real outdoor recordings of a DJI Air 3S. The 100 m position is used for development; recordings at nominal ranges of 150 and 200 m are reserved for evaluation with disjoint background calibration intervals. Across 600 held-out aircraft windows, DCCR changes the mean spherical discrepancy from nominal reference directions from {{PHAT_MEAN}}° for SRP-PHAT to {{RANK_MEAN}}°. At independently calibrated operating thresholds, its detection rate is {{RANK_TPR}}% and its false-alarm rate is {{RANK_FPR}}% over 200 background windows. With the same DCCR detector gate, the fraction of aircraft windows both detected and localized within 10° changes from {{SHARED_PHAT_JOINT}}% to {{RANK_JOINT}}%. These results characterize source association on four aircraft recordings, rather than independent trials at every window. The nominal static references, single aircraft, single acquisition day, and location-specific calibration delimit the demonstrated scope.

**Index terms** — UAV acoustics, microphone array, direction of arrival, SRP-PHAT, spatial coherence, candidate ranking.

## I Introduction

Passive acoustic sensing provides a direct observation of the sound radiated by a small rotorcraft. Its usefulness depends on extracting aircraft-related evidence from environmental sound and associating that evidence with a bearing [1]. These are distinct tasks. A strong spatial peak establishes that some component is spatially consistent with a source; it does not identify the source as a UAV. Wind, vehicles, machinery and other coherent backgrounds can therefore affect both the alarm decision and the selected bearing.

Generalized cross-correlation and steered response power (SRP) provide interpretable mechanisms for combining microphone delays [2], [3]. Phase-transform weighting sharpens the spatial response, but it gives substantial influence to frequency bins that may contain little aircraft energy. Existing SRP extensions address spectral reliability, spatial search and multiple-source processing [4]. An additional issue arises when a plausible aircraft bearing is present in the spatial map but is not its strongest peak. Multiplying the entire map by a single positive detector score cannot change its maximizer.

This work addresses that association step using a compact supervised model. SRP-PHAT first proposes several directions without access to aircraft labels or reference angles. Each direction is then represented by a frequency profile of steered, normalized cross-spectral coherence. A linear ridge score learns which profiles correspond to the aircraft, including contrast against incorrect directions in the same aircraft recording. The highest-scoring candidate supplies both the bearing and a detection score. The resulting method is termed direction-conditioned coherence ranking, or DCCR.

The contribution is an explicit, reproducible association mechanism built on established array-processing components. It combines a 24-dimensional directional representation, within-recording hard negatives, and an audio-only candidate search. A held-out field comparison isolates the effect of association by applying the same detector gate to conventional and ranked bearings. The study uses measured 208-channel recordings rather than substituting a synthetic sound field for experimental evidence. Its restricted acquisition diversity permits a focused algorithmic comparison, while requiring precise limits on generalization.

## II Related Work

Knapp and Carter established generalized correlation as a framework for time-delay estimation [2]. SRP projects pairwise delay evidence into a spatial search and remains a practical basis for acoustic localization [3], [4]. PHAT, smoothed-coherence-transform (SCOT) normalization, and reliability weighting represent different compromises between amplitude information and phase robustness. These operations are established signal-processing choices, not contributions introduced by DCCR.

Valin et al. incorporated noise-dependent reliability into beamforming and combined localization with particle tracking [5]. Donohue et al. investigated partial phase-transform weighting in noisy and reverberant environments [6]. Brümann and Doclo showed how coherent noise can impair compact-array SRP and studied an auxiliary-microphone construction [7]. These methods motivate distinguishing a reliable coherent component from an aircraft-specific component. The present implementation uses neither an auxiliary microphone nor a particle tracker.

UAV-specific work exploits rotor-related spectral structure. Uluskan studied SRP around drone harmonics [8], while Yang et al. investigated neural localization using signal synthesis and real drone audio [9]. DCCR uses fixed frequency bands and does not estimate a blade-passing frequency. Its learned score is deliberately small enough to fit the available development recordings; it is not presented as a replacement for neural methods trained on substantially larger corpora. Documented datasets such as DDL and UaVirBASE also emphasize the role of acquisition geometry and localization references [10], [11]. The nominal diagrams available for the present recordings support static bearing comparisons, but not trajectory-level tracking evaluation.

Candidate-dependent spectral evidence distinguishes DCCR from attaching a window-level detector to a single SRP maximum. Wrong-direction training examples are drawn from the same aircraft audio as the positive examples. Consequently, file-level background or global amplitude alone cannot separate those examples. This design does not eliminate every possible dataset shortcut, but it makes source association an explicit part of the learning objective.

## III Signal Model and Directional Representation

### A Array and coordinate model

Let the position of microphone m be the three-dimensional vector r_m. For a sufficiently distant source in unit direction u, the received signal is approximated by

$$ x_m(t)=a_m s(t+\mathbf{r}_m^{T}\mathbf{u}/c)+v_m(t). $$ (1)

Here c is the speed of sound, a_m is a channel gain, and v_m includes background sound and sensor noise. The implementation uses c = 343 m/s. The 0.30 m aperture is small relative to the nominal 100–200 m source ranges, so the estimation target is bearing rather than range. A planar array has a mirror ambiguity across its plane; the search is restricted to the upper hemisphere because the aircraft is above the array.

Azimuth a increases clockwise from the device reference mark, and elevation e is measured above the array plane. In the native coordinates supplied with the array geometry, zero azimuth is negative y and 90° is negative x. The corresponding unit vector is

$$ \mathbf{u}(a,e)=(-\cos e\sin a,-\cos e\cos a,\sin e)^{T}. $$ (2)

The physical geometry is used directly for steering. Pixel-to-angle approximations from a camera display are not used in the estimator. Near the zenith, a small change in horizontal projection can produce a large azimuth change; spherical angular discrepancy is therefore the primary localization measure.

### B Cross-spectral estimates

Each 200 ms observation is centered separately by channel and resampled from 48 to 16 kHz with an anti-aliasing polyphase filter. A 512-sample periodic Hann window and a 256-sample hop produce eleven short-time Fourier frames within the observation. Each short frame is also centered. The analyzed frequency bins span 300–7500 Hz. If X_m(l,k) is the complex spectrum of short frame l, the averaged cross- and auto-spectra are

$$ R_{ij}(k)=L^{-1}\sum_{l=1}^{L}X_i(l,k)X_j(l,k)^{*},\qquad P_i(k)=R_{ii}(k). $$ (3)

The complex coherence-normalized spectrum and PHAT spectrum are

$$ C_{ij}(k)=\frac{R_{ij}(k)}{\max(\sqrt{P_i(k)P_j(k)},\epsilon)},\qquad Q_{ij}(k)=\frac{R_{ij}(k)}{\max(|R_{ij}(k)|,\epsilon)}. $$ (4)

The numerical floor is 10⁻¹² times the mean in-band channel power, with a minimum of 10⁻³⁰. Averaging precedes normalization. Thus coherence is not computed from a single outer product, which would have unit magnitude wherever both channels are nonzero.

All 208 channels participate in a fixed set of 1124 pairs. Pairs are constructed from channel-index offsets 17, 35, 53, 71, 89 and 103 modulo 208, deduplicated, and restricted to baselines of at least 0.06 m. The rule depends only on channel order and geometry. The same pair set is used by every compared method, so pair reduction is not credited as a DCCR-specific accuracy gain.

### C Bearing proposals

For pair set P and analyzed frequency set F, the PHAT spatial score is proportional to

$$ B(\mathbf{u})=\sum_{(i,j)\in\mathcal{P}}\sum_{k\in\mathcal{F}}\operatorname{Re}\{Q_{ij}(k)e^{-j2\pi f_k(\mathbf{r}_i-\mathbf{r}_j)^{T}\mathbf{u}/c}\}. $$ (5)

The sign follows (1): an earlier arrival at the microphone closer to the source gives a positive cross-spectral phase, which steering cancels. A 1257-point grid uniformly samples the horizontal direction-cosine disk at spacing 0.05. The vertical component is the nonnegative square root needed for unit length. The four highest-scoring grid candidates separated by at least 12° are retained. Each is refined in a ±0.05 neighborhood of horizontal direction cosines at spacing 0.005, followed by a local angular refinement at 0.1° spacing. The angular neighborhood spans ±1° in azimuth and ±2° in elevation. The resulting bearing is not claimed to have 0.1° physical accuracy; that value is only a numerical search step.

The implementation evaluates inverse-FFT correlation tables with eightfold interpolation and linear lag lookup. Pairwise phase tests at five known upper-hemisphere directions produced discrepancies below 0.054°. These deterministic checks verify the sign and numerical search, not the accuracy of real measurement labels.

### D Direction-conditioned coherence bands

The analysis band is divided into 24 adjacent 300 Hz bands, including the final 7500 Hz bin. For candidate u, feature b is

$$ f_b(\mathbf{u})=\frac{1}{|\mathcal{P}|\,|\mathcal{F}_b|}\sum_{(i,j)\in\mathcal{P}}\sum_{k\in\mathcal{F}_b}\operatorname{Re}\{C_{ij}(k)e^{-j2\pi f_k(\mathbf{r}_i-\mathbf{r}_j)^{T}\mathbf{u}/c}\}. $$ (6)

This signed response measures how strongly each frequency region supports that particular direction. It retains frequency-dependent coherence rather than reducing all bins to one broadband peak. Away from the numerical floor, positive channel gains cancel between cross- and auto-spectra. A common amplitude change therefore leaves the representation unchanged. On a development observation, amplitude factors 0.001, 17 and 1000 changed the final score by less than 1.1 × 10⁻⁷ and did not change the selected bearing.

The model receives only these 24 values. It receives no azimuth, elevation, range, recording identifier, absolute power, camera image or reference direction. Geometry enters through the physical steering operation, not through a learned coordinate prior.

![Figure 1. Array geometry and the learned directional-coherence model. All 208 channels enter the shared pair construction. Coefficients describe standardized frequency-band features and are learned exclusively from the development position.](../figures/field/geometry_weights_en.png)

## IV Learning and Joint Inference

### A Training examples and hard negatives

The two aircraft recordings at the 100 m development position provide positive observations. For each observation, the nominal reference direction is used as an additional training beam. PHAT proposals within 5° of that reference are also positive. Proposals at least 15° away are hard negatives; proposals between these bounds are excluded to limit ambiguous supervision. Background observations provide negative proposals. Reference-steered beams are used only to form training examples. They are never inserted into the candidate set during held-out inference.

The development set comprises 300 aircraft windows and 100 background windows. It yields 1779 labeled directional examples: 598 positive and 1181 negative. There are 781 wrong-direction negatives from aircraft windows and 400 proposals from background windows. Examples from a given observation remain together in model selection. Two grouped folds each hold out one entire aircraft recording and one contiguous 10 s half of the development background. Because those background halves belong to one recording, this internal validation is not an independent-background generalization test.

### B Regularized ranking model

Feature means and standard deviations are estimated within each training fold with class-balanced weights. Standard deviations are floored at 0.01. With z_n denoting a standardized feature vector and y_n ∈ {−1,+1}, the fitted model minimizes

$$ \sum_{n=1}^{N}w_n(\boldsymbol{\beta}^{T}\mathbf{z}_n+b-y_n)^2+\lambda\|\boldsymbol{\beta}\|_2^2. $$ (7)

Each class has total weight N/2. The intercept is not penalized. Ridge strengths 0.1, 1, 10 and 100 are compared using the balanced candidate-level squared error on the two held-out folds. The selected value is 100. The final model is refitted on all permitted development examples. The score is a regression score for ranking and thresholding, not a calibrated posterior probability.

The hard-negative ablation removes only the 781 incorrect directions from aircraft windows. It retains the same feature representation, inference proposals and calibration rule, and independently selects ridge strength 10 using the same fold procedure. This comparison tests whether exposing the model to competing directions in the same audio improves association.

### C Inference and threshold calibration

For the four audio-generated and refined candidates, DCCR computes

$$ s_q=\boldsymbol{\beta}^{T}[(\mathbf{f}(\mathbf{u}_q)-\boldsymbol{\mu})/\boldsymbol{\sigma}]+b,\qquad q^{*}=\operatorname{argmax}_{q}s_q. $$ (8)

The selected unit vector is u_q* and the detection score is s_q*. Thresholds are separately calibrated for each method and evaluation location using the same 25 background windows. For nominal upper-tail level α = 0.05, the rank ceil((25+1)(1−α)) is 25. Detection requires a score strictly greater than the largest calibration score. Equality is rejected. This is an empirical operating-point rule: temporally correlated, nonstationary background windows do not establish the exchangeability needed for a formal 5% false-alarm guarantee.

All positive windows receive a bearing estimate, including those rejected by the detector. Localization results therefore do not improve artificially by discarding difficult rejected observations. Joint success is evaluated separately as detection together with an angular discrepancy of at most 10°.

## V Field Experiment

### A Recordings and reference information

The acoustic measurements were acquired on 25 May 2026 with a horizontally placed, upward-facing CRY8501/SonoCam Pi array and a DJI Air 3S [12]. The archive contains nine recordings: two aircraft recordings and one background recording at each of three positions. Each recording consists of 208 synchronized-acquisition channel files at 48 kHz and 16-bit PCM. Actual file durations range from 30.30 to 30.50 s, totaling 273.75 s. The stored polar microphone coordinates yield a maximum radius of 0.1499944 m. Matching channel formats and sample counts were verified across all 1872 WAV files, and no sample reached the PCM clipping limits. Matching headers do not independently establish microphone phase calibration or clock-skew accuracy.

Channel-dependent DC offsets are present, motivating the uniform centering operation. No channel was excluded after examining localization outcomes. The videos and device imaging outputs are not estimator inputs or ground-truth substitutes. Reference azimuths and elevations are taken from the acquisition diagrams in Table I. Their uncertainty and any within-recording hovering displacement are not quantified by synchronized trajectory logs. The reported errors are consequently discrepancies from nominal static directions.

**Table I. Recording groups and nominal directions. Each group contains two approximately 30 s aircraft takes and one approximately 30 s background recording.**

| Group | Nominal range | Azimuth take 1 / take 2 | Elevation | Role |
|---|---|---|---|---|
| P1 | 100 m | 225.00° / 251.50° | 88.3° | Development |
| P2 | 150 m | 97.17° / 92.41° | 60.0° | Held-out evaluation |
| P3 | 200 m | 131.88° / 135.00° | 66.4° | Held-out evaluation |

The first 30 s of each aircraft recording is used; short tails are excluded uniformly. For each background recording, [0,5) s estimates a noise reference where required, [5,10) s calibrates detection, and [10,30) s supplies background evaluation windows. The primary evaluation therefore contains 600 aircraft and 200 background windows from P2 and P3, plus 50 separate calibration windows. P1 results are development diagnostics and are not pooled into these totals. The availability of a short local background calibration is an explicit operating assumption.

### B Baselines and attribution

The principal baselines are SRP-PHAT, SCOT-SRP using C_ij from (4), and coherence-weighted PHAT. The latter multiplies Q_ij by clip((L|C_ij|²−1)/(L−1),0,1), a finite-snapshot shrinkage heuristic rather than an exact unbiased estimator under overlapping Hann frames. All use the same geometry, pair selection, analysis band and search refinements.

A reference-assisted variant is also retained. It estimates background auto- and cross-spectra from the designated reference interval, aligns each channel by the median current-to-reference in-band power ratio, subtracts the scaled background cross-spectrum, and weights the residual phase by bounded residual coherence and nonnegative excess-power reliability. Exact operations are included in the reproduction code. This is a simple subtraction baseline, not a reproduction of the adaptive estimator in [5]. Its poor development behavior motivated retaining a comparison that tests, rather than assumes, the benefit of background subtraction.

The no-hard-negative DCCR model uses exactly the same candidate features at evaluation. In addition to each method's own detector, a paired comparison applies the full DCCR detector decision to every baseline bearing. This separates changes in source association from changes in the alarm threshold. The best possible candidate discrepancy is recorded as an oracle diagnostic after inference, never as the estimator output.

### C Measures and reproducibility

For estimated and reference unit vectors, the angular discrepancy is

$$ e_{\mathrm{ang}}=\frac{180}{\pi}\arccos[\operatorname{clip}(\widehat{\mathbf{u}}^{T}\mathbf{u}_{\mathrm{ref}},-1,1)]. $$ (9)

Mean, median, 95th percentile and fractions within 5° and 10° summarize localization. Detection rate and false-alarm rate use the designated aircraft and background windows, respectively. Equal recording durations make the aggregate aircraft mean equally weighted across four recordings. Adjacent windows remain temporally dependent. Window-level binomial intervals or an independent-window bootstrap would overstate the effective sample size, so the main comparison is descriptive and reports the four recording-level paired differences explicitly.

Code, model, protocol, feature-cache and input-manifest hashes were frozen before held-out execution. The models were not revised after reading held-out outputs. Verification covers array phase conventions, cached-feature reconstruction, ridge-equation residuals, amplitude invariance, threshold inequalities, complete pairing and summary reconstruction. Runtime measurements use an Intel Core i7-12700KF workstation, Python 3.12.14, NumPy 2.2.6 and SciPy 1.15.3, with numerical-library threads requested as one. Wall-clock times are collected during the comparison run, not an isolated timing benchmark. They exclude file I/O; the 200 ms acquisition window is additional to computation. Baseline timings conservatively include the shared spectral-weight builder. The no-hard-negative timing also includes shared candidate preparation and is an upper bound for its standalone implementation.

## VI Results

### A Bearing estimation and source association

{{LOCALIZATION_RESULTS}}

**Table II. Held-out localization discrepancy from nominal directions over all 600 aircraft windows. Rejected windows remain included.**

{{LOCALIZATION_TABLE}}

{{RECORDING_RESULTS}}

**Table III. Mean angular discrepancy by held-out aircraft recording. Positive differences indicate an improvement over SRP-PHAT.**

{{RECORDING_TABLE}}

![Figure 2. Descriptive angular-discrepancy distributions and calibrated detection operating points on the held-out recordings. The angular axis is logarithmic above 1°. DCCR and its ablation have nearly overlapping distribution curves. Windows are temporally correlated.](../figures/field/performance_en.png)

### B Detection and shared-gate comparison

{{DETECTION_RESULTS}}

**Table IV. Held-out detection and joint outcomes. TPR is based on 600 aircraft windows; FPR is based on 200 background windows. Each method uses its own background-calibrated threshold.**

{{DETECTION_TABLE}}

{{JOINT_RESULTS}}

### C Ablation and computational cost

{{ABLATION_RESULTS}}

{{TIMING_RESULTS}}

![Figure 3. Window-wise angular discrepancies for the four held-out aircraft recordings. The vertical axes are logarithmic above 1°. Both estimators process the same observations; no temporal smoother or tracking model is applied.](../figures/field/recordings_en.png)

## VII Discussion

The ranking formulation changes the quantity being optimized. PHAT searches for broadband phase agreement, whereas DCCR compares frequency-dependent agreement against a learned aircraft representation at each proposed direction. Including wrong directions from the same aircraft observation exposes the model to examples that share the global spectrum, environmental context and recording gain with the positive beam. The shared-detector comparison in Section VI evaluates the ranking mechanism without crediting it for a different alarm decision. The hard-negative ablation supports a detection benefit at the selected operating point, but provides no separate bearing-accuracy gain.

The reduction in mean discrepancy is driven by fewer gross departures from the nominal direction. The pooled median changes only from 3.49° to 3.47°, while the 95th percentile remains 54.16°. In P3 take 2, 33 of 150 estimates still exceed 10°. Across all aircraft windows, 34 of the 36 discrepancies above 10° already lack a within-10° candidate. Relative to the nominal references, the remaining tail is therefore predominantly a proposal-coverage limitation. Small systematic offsets in otherwise stable estimates, and any contribution from aircraft motion, cannot be isolated without more accurate, synchronized reference measurements.

The field experiment also exposes a limitation of direct reference subtraction. A background recording acquired earlier is not an exact noise realization for a later aircraft recording. Scaling its average spectrum cannot reconstruct changing vehicles, wind or other transients. Subtraction can attenuate useful bins or leave a misleading residual. DCCR avoids subtracting a presumed contemporaneous waveform, but its learned spectral signature remains sensitive to changes in aircraft type, operating state, propagation and sensor response.

Several limits constrain interpretation. First, the test includes one aircraft model, one acquisition day and two held-out positions. The six held-out recordings are the relevant units of evidence; the 800 analyzed test windows do not create 800 independent field trials. Second, the calibration background comes from the same location as its test recordings, so results do not establish calibration-free transfer to a new environment. Third, the reference directions are nominal static values. Hovering motion, orientation registration, sound-speed error and microphone phase mismatch can all contribute to the reported discrepancy. Fourth, the negative material consists of the recorded backgrounds and is not an exhaustive collection of confusing machinery, aircraft or simultaneous sources.

DCCR also inherits the proposal stage's coverage limit. If SRP-PHAT fails to include a useful aircraft direction among the four proposals, a ranker cannot recover it. Increasing the number of proposals or introducing several spatial front ends could improve coverage, but would change both computational cost and the training distribution. Such changes require new development data and a fresh held-out evaluation rather than retrospective tuning on the present results.

The method estimates a bearing and an empirical acoustic-presence score. It does not estimate range, authenticate an aircraft identity, separate several simultaneous UAVs, or validate a motion tracker. Measured computation on a workstation likewise does not establish embedded-device latency. These boundaries leave a concrete result: an implemented direction-conditioned association method compared on real multichannel aircraft recordings under a fixed protocol.

## VIII Conclusion

{{CONCLUSION}}

## Data and Code Availability

The reproducibility package contains the array reader, inference and training code, frozen models, development-selection records, input hashes, per-window predictions, candidate scores and scripts that regenerate the tables and figures. The measured recordings retain their original channel files and acquisition documents. Their original provider's distribution conditions apply; no unrestricted public redistribution license is asserted. No synthetic observation is included in the field results.

## References

{{REFERENCES}}
