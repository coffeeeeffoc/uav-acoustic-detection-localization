# Source-Conditioned Candidate Ranking for Acoustic Detection and Localization of Small UAVs

## Abstract

Strong mechanical sound can produce a larger acoustic-array response than a small unmanned aerial vehicle (UAV), causing a conventional peak-picking localizer to report the interferer's direction. This paper proposes source-conditioned candidate ranking to distinguish target association from acoustic-source prominence. Multiple spatial maps generate competing directions; ordinary and interference-suppressed beam spectra then describe each candidate, and a compact supervised ranker selects the direction with the strongest target-specific evidence. A separate amplitude-invariant spectral-spatial detector is trained with both individual and multiple interfering sources. The method is evaluated on independently generated multichannel recordings after freezing development choices and calibrating every detector with the same negative observations. Across 1000 target-present static trials, the proposed localizer reduces mean spherical error from {{PHAT_MEAN}} to {{PROPOSED_MEAN}} degrees and raises the fraction within 10 degrees from {{PHAT_WITHIN}}% to {{PROPOSED_WITHIN}}%. The detector obtains {{TPR}}% recall at {{FPR}}% false alarms on 2000 negative trials that include multiple mechanical and broadband sources. Joint detection and localization within 10 degrees reaches {{JOINT}}%. Ablations isolate spatial features and interference-suppressed candidate descriptions. Complete audio, fitted models, source hashes and per-trial estimates accompany the study. The gains establish algorithmic improvement within the declared simulation distribution; field performance and physical detection range remain unverified.

**Index terms:** unmanned aerial vehicle; acoustic detection; microphone array; source association; SRP-PHAT; interference suppression; candidate ranking.

## I Introduction

Low-altitude, slow-moving, small unmanned aerial vehicles motivate passive acoustic sensing that complements optical, radio-frequency and radar observations. Rotor and motor sound can be observed without a cooperative transmission from the aircraft. The main difficulty is not simply finding an acoustic source: an array may localize a ground engine very accurately while missing the UAV. Detection must therefore identify target-related evidence, and localization must associate a spatial hypothesis with that target rather than automatically select the strongest source [1].

Generalized cross-correlation with phase transformation (GCC-PHAT) and steered response power with PHAT weighting (SRP-PHAT) provide interpretable spatial estimators [2, 3]. Harmonic concentration and microphone-pair coherence can emphasize useful bins, but a coherent periodic interferer can satisfy both criteria. Once a global fundamental estimate follows the interferer, sharpening its harmonic mask can strengthen the wrong spatial maximum. A detector based only on harmonic contrast and coherence inherits a related ambiguity. These observations motivate separating spatial candidate generation from target-specific candidate selection.

This paper proposes source-conditioned candidate ranking (SCCR). Several complementary spatial maps retain competing hypotheses instead of committing to one peak. Each direction is described using the mixture spectrum, a beam steered toward it, and a two-direction interference-suppressed beam. A supervised, fixed-size Gaussian-basis regressor predicts candidate quality from these descriptions. An independent frame detector combines normalized spectral structure with spatial covariance statistics and is trained with multiple-source negative mixtures. The final output includes a detection decision and a bearing; the latter is evaluated over all positive observations as well as through the detection gate.

The contributions are an implemented candidate-association mechanism for competing acoustic sources; a detector-development procedure that explicitly includes multiple-source negatives and excludes absolute-amplitude shortcuts; and paired evidence separating detection, raw localization and their joint success. The method builds on established beamforming and supervised learning. Its claim is a specified, reproducible improvement over the tested reference implementation, rather than priority for harmonic processing or general superiority over every UAV system.

## II Related Work

### A Spatial localization and frequency weighting

The generalized correlation framework estimates inter-sensor delays [2], while SRP evaluates the delays predicted by spatial hypotheses [3]. Recent tutorial work reviews robustness, time-frequency weighting and efficient search in this family [4]. MUSIC instead uses signal and noise subspaces [5]. Holding the array, search grid and observation blocks constant enables a focused SRP comparison without attributing every difference to a different estimator architecture.

Partial phase normalization retains spectral magnitude information [6]. Noise-aware beamforming can weight whitened correlations using reliability estimates [7], and additional sensors provide further spatial information [8]. Harmonic-focused SRP for drone localization and tracking is explicit prior work [12]. Consequently, merely multiplying PHAT by a harmonic or coherence weight is not the contribution here. SCCR changes how competing spatial peaks are associated with the target after map construction. Frequency weighting supplies hypotheses; source-conditioned features determine their ordering.

### B Acoustic target discrimination

Measured and synthesized multirotor sound combines tonal structure, broadband components and amplitude/frequency modulation [9, 21]. These motivate spectral descriptors, but do not imply a universal spectral boundary between a UAV and machinery. Finite observation duration, masking and similar rotor speeds can make neighboring harmonic families unresolved. Zero-padding improves frequency-grid interpolation, not physical resolving power.

Synthesis-informed neural localization has been evaluated using both simulated and real UAV recordings [10]. Reviews of learning-based sound localization describe many alternative input representations and output formulations [11]. Recent multichannel studies include uncertainty-aware drone detection/localization and learned acoustic imaging [13, 14]. The EchoHawk preprint combines harmonic processing, spectral classification and several classical array estimators, and emphasizes recording-session separation [20]. It is particularly close at the pipeline level. The distinction examined here is target-conditioned ordering of competing directions, including spectra formed after suppressing a competing direction, together with pure multiple-source negatives in detector development.

### C Data and validation scope

Ground-array resources include UaVirBASE and multichannel UAV recordings with synchronized flight information [15, 16]. UAV-mounted audition resources such as DREGON and DroneAudioset address a different source-placement and ego-noise problem [17, 18]. Dataset names alone cannot establish label compatibility. A licensed IDMT recording is archived as supplementary signal material [19], but is not used for fitting or numerical performance claims. Its available elevation placeholders are unsuitable as three-dimensional reference directions. The quantitative study below is a simulation experiment with complete retained observations.

## III Observation Model and Spatial Proposals

### A Geometry and common front end

Eight nonuniform microphones form a planar array of approximately 0.40 m aperture. Azimuth increases counterclockwise from the positive horizontal x axis, and elevation is measured above the array plane. The upper-hemisphere direction vector is

$$\mathbf{u}(\theta,\phi)=[\cos\phi\cos\theta,\ \cos\phi\sin\theta,\ \sin\phi]^T.$$ (1)

For nominal microphone position r_m and sound speed c = 343 m/s, the far-field relative delay is

$$\tau_{ij}(\mathbf{u})=-\frac{(\mathbf{r}_i-\mathbf{r}_j)^T\mathbf{u}}{c}.$$ (2)

The negative sign corresponds to a direction pointing from the array toward the source. A source above and its mirror below a planar array produce the same direct-path delays; the upper-hemisphere restriction encodes the stated application prior. Near-horizontal elevation and near-zenith azimuth remain poorly conditioned. The method estimates bearing, not physical range.

Each observation contains 1600 samples per channel at 8 kHz, corresponding to a nonoverlapping 0.2 s block. After mean removal, five 512-sample periodic Hann windows with 256-sample spacing produce STFT coefficients X_m(l,k). Define

$$G_{ij}(k)=\frac{1}{5}\sum_{l=1}^{5}X_i(l,k)X_j^*(l,k),\quad Q_{ij}(k)=\frac{G_{ij}(k)}{\max(|G_{ij}(k)|,\epsilon)}.$$ (3)

Only 200–3000 Hz contributes to spatial search. All 28 microphone pairs are used. A 4096-point inverse real FFT supplies eightfold lag-grid oversampling, followed by linear interpolation at (2). For a frequency weight w_ij and the corresponding generalized correlation r_ij,w, a map is

$$R_w(\mathbf{u})=\sum_{i<j}r_{ij,w}(\tau_{ij}(\mathbf{u})).$$ (4)

The fixed grid contains 3601 directions: 120 azimuths in 3-degree steps, 30 elevations from 0 to 87 degrees, and one zenith point. Identical geometry and grid are used for every reference and proposed direction estimate.

### B Complementary proposal maps

SCCR forms five maps. The first is conventional PHAT. The second uses the complete 1600-sample Hann-windowed block, a 12800-point inverse transform, and a soft spectral-excess weight. With P_k denoting the mean channel power and F_k its 31-bin running median,

$$e_k=\max(P_k/\max(F_k,\epsilon)-1,0),\quad w_k^{E}=0.005+0.995\frac{e_k}{1+e_k}.$$ (5)

The remaining three maps correspond to distinct estimated harmonic hypotheses. A 2048-point transform of the normalized full block supplies mean channel power. Running-median normalization, log(1 + P/F) minus log(2), and Gaussian smoothing with one-bin standard deviation produce contrast z_k. Fundamentals from 80 to 240 Hz in 2 Hz steps receive scores

$$H(f)=\frac{\sum_{h=1}^{12}h^{-1/2}z_{\operatorname{round}(hfN_F/f_s)}}{\sum_{h=1}^{12}h^{-1/2}}.$$ (6)

The three largest candidates separated by at least 20 Hz are retained. Each defines a soft mask with floor 0.02 and a Gaussian width max(8 Hz, 0.012f_k) around its nearest harmonic. These masks weight the shared short-window PHAT spectrum. Unlike a single-comb decision, alternative hypotheses can preserve target-related bins even when an interferer receives the highest global harmonic score.

The PHAT map contributes up to three maxima, and each other map up to two. Within a map, selected directions suppress neighbors within 20 degrees of spherical angle; candidates within 7 degrees of an already retained direction are merged. The resulting list contains at most eleven hypotheses. The original PHAT maximum remains available, so improvement must arise from selecting a better-supported alternative, not removing a difficult baseline observation from evaluation.

## IV Source-Conditioned Ranking and Detection

### A Candidate beam spectra

Let tau_m(u) = -r_m^T u/c and let X_m(k) be the 2048-point full-block transform after channel-mean removal and shared RMS normalization. The delay-and-sum spectrum toward candidate u is

$$B_{\mathbf{u}}(k)=\frac{1}{8}\sum_{m=1}^{8}e^{j2\pi f_k\tau_m(\mathbf{u})}X_m(k).$$ (7)

For each candidate, the strongest competing PHAT candidate more than 15 degrees away provides direction v. The steering overlap is

$$a_{uv}(k)=\frac{1}{8}\sum_{m=1}^{8}e^{j2\pi f_k[\tau_m(\mathbf{u})-\tau_m(\mathbf{v})]}.$$ (8)

A regularized two-direction constrained combination suppresses the competing direction:

$$\widetilde B_{\mathbf{u}}(k)=\frac{B_{\mathbf{u}}(k)-a_{uv}(k)B_{\mathbf{v}}(k)}{\max(1-|a_{uv}(k)|^2,0.1)}.$$ (9)

Without regularization and model mismatch, the numerator cancels a source exactly aligned with v and the denominator restores the response at u. The floor limits amplification when the steering vectors are nearly dependent. This is a two-direction suppression feature, not a claim of arbitrary-source separation. Calibration mismatch, reverberation and closely spaced directions can prevent accurate cancellation.

### B Candidate descriptions and supervised association

Each candidate receives 149 features. Three 42-dimensional spectral descriptions represent the mixture, its ordinary beam and its suppressed beam. Each description contains relative band energies, flatness, entropy, contrast quantiles and dispersion over five bands; four harmonic-score summaries; and energy fractions within 5, 10 and 20 Hz of the best estimated harmonic comb. The five bands are 80–3000, 80–400, 400–1000, 1000–2000 and 2000–3000 Hz. Twelve features describe beam-to-mixture power ratios and suppressed-to-ordinary power ratios over 200–800, 800–1600 and 1600–3000 Hz. Ten summarize the five map values and their normalized counterparts, and one measures separation from the nearest retained candidate. These descriptors do not contain the true direction, source count, nuisance label, SNR or true fundamental.

During supervised development only, a candidate with spherical target error e in a positive recording receives the continuous quality label

$$y(e)=\exp[-(e/10^{\circ})^2],\qquad y=0\ \text{for target-absent recordings}.$$ (10)

Features are standardized using training-fold means and standard deviations, with a scale floor of 0.05 and clipping to ±8. Up to 128 anchors from candidates with quality at least exp(-1) and 128 from the remaining candidates form Gaussian basis functions. For d standardized features and anchor a_j,

$$\psi_j(\mathbf{z})=\exp\left[-\frac{\|\mathbf{z}-\mathbf{a}_j\|^2}{2d\sigma^2}\right],\quad \sigma=1.$$ (11)

An intercept is appended. Weighted ridge regression solves

$$\boldsymbol{\beta}=(\Psi^T W\Psi+0.1I)^{-1}\Psi^T W\mathbf{y}.$$ (12)

Candidates above the quality boundary receive a weight equal to the ratio of the remaining count to their count; other weights are one. Every candidate belonging to an observation remains in the same development fold. Standardization, anchors and regression weights are fitted using training folds only. The final model is refitted on the complete development partition. At inference, the candidate with maximum predicted quality supplies the bearing; its score is not treated as a calibrated aircraft probability.

### C Amplitude-invariant frame detection

The detector first removes channel means and divides the entire block by its shared RMS. It uses 39 spectral features and 48 spatial features. The spectral features comprise the first 39 elements of the mixture description above, with harmonic samples averaged after multiplication by h^(-1/2). Spatial features summarize covariance at 512- and 1024-sample STFT resolutions. For each frequency, covariance is averaged over available windows; its eigenvalues are normalized by their sum. Pairwise magnitude-squared coherence is

$$\gamma_{ij}(k)=\frac{|C_{ij}(k)|^2}{\max(C_{ii}(k)C_{jj}(k),\epsilon)}.$$ (13)

After clipping to the unit interval, coherence is averaged over microphone pairs. Its 25th, 50th and 90th percentiles, the means of the largest two normalized eigenvalues, and the standard deviation of the largest eigenvalue are measured over four bands at each resolution: 200–3000, 200–800, 800–1600 and 1600–3000 Hz. These statistics complement spectral shape without encoding absolute recording level. Spectral/covariance normalization floors are 10 to the power of -15; the PHAT denominator floor is 10 to the power of -20.

A Gaussian-kernel ridge detector standardizes the features with scale floor 0.05 and predicts a real-valued score. With training labels t equal to +1 or -1,

$$\boldsymbol{\alpha}=(K+\lambda I)^{-1}\mathbf{t},\quad D(\mathbf{z})=\sum_n\alpha_n\exp\left[-\frac{\|\mathbf{z}-\mathbf{z}_n\|^2}{2d\sigma^2}\right].$$ (14)

Bandwidths 1, 2 and 4 and regularization values 0.01, 0.1 and 1 are compared using internal development AUC. Both the full 87-feature detector and its 39-feature spectral ablation select sigma = 1 and lambda = 0.01. Their final models use 2800 development observations. The feature-only ablation shares the full extraction implementation and therefore does not establish a feature-extraction speed advantage.

Multiple-source negatives are essential: adding another coherent source changes covariance even when neither source is a UAV. Detector development therefore includes engine–engine, broadband–broadband, engine–broadband and engine–broadband–engine mixtures. No constituent recording crosses the internal training/validation boundary. Inference accepts only audio and fitted parameters.

### D Frozen decisions and joint output

Each detector is calibrated independently on the same 800 target-absent observations. For nominal false-alarm level alpha = 0.05, the threshold is

$$T=D_{(761)},\quad 761=\lceil(800+1)(1-0.05)\rceil,\quad \widehat b=\mathbf{1}[D>T].$$ (15)

The same proposed detector gates PHAT and SCCR when isolating localization's contribution to joint success. The system retains a raw direction even when the decision is negative for unconditional analysis; this is not counted as an accepted detection. A frozen threshold controls the declared negative mixture empirically, not every possible environment.

![Figure 1. Processing structure. Multiple acoustic maps propose directions; source-conditioned spectra determine candidate quality. The frame detector uses separate global spectral-spatial features and a frozen threshold.](../figures/improved_pipeline.png)

## V Experimental Protocol

### A Signals and independent partitions

The generator uses a nonuniform planar eight-microphone geometry, 24 kHz waveform synthesis and time-domain interpolation to the 8 kHz observations. Target sound contains four perturbed rotor-like harmonic series and a stochastic band-limited component. Base frequency is uniform from 85 to 230 Hz, and the nominal tonal mixing fraction ranges from 0.55 to 0.85. An engine-like nuisance uses one more stable harmonic series with tonal fraction 0.82–0.95. The other nuisances are independent sensor noise, low-pass wind-like noise and directional broadband noise. These analytic classes are not validated aircraft or engine emission models.

Propagation uses spherical geometric distances from 20 to 80 m, while steering uses far-field delays. Target amplitude is subsequently normalized to impose SNR, so distance controls wavefront curvature only and cannot establish detection range. Sound speed varies from 338 to 348 m/s, channel gain has 0.6 dB standard deviation, and target mixtures contain an artificial redirected echo of relative amplitude 0.05–0.25 and delay 3–12 ms. SNR denotes direct-target energy divided by the full nuisance energy across channels and samples, before adding the echo. Positive trials use -15, -10, -5, 0 and 5 dB. Reference directions are uniform over upper-hemisphere solid angle.

Table I. Development, calibration and independent evaluation units. Augmented development mixtures never cross constituent-recording folds.

| Partition | Observations | Role |
|---|---|---|
| Original development | 1000 positive + 1000 negative | Candidate training; detector development |
| Added development negatives | 800 mixtures | 4 multi-source groups; 150 training + 50 validation per group |
| Fresh calibration | 800 negative | 8 groups × 100; one frozen threshold per detector |
| Fresh static test | 1000 positive + 2000 negative | 4 × 5 × 50 positives; 8 × 250 negatives |
| Continuous stress test | 24 sequences × 24 s | 4 scenes × 3 SNRs × 2 realizations |

The original development partition includes previously examined experiments; none of its outcomes is presented as independent final-test evidence. For the detector, an internal class-stratified split contains 1500 original training items and 500 validation items, supplemented by 600 and 200 negative mixtures respectively. Candidate association uses five folds grouped by complete original recording. The final parameters, model files and source hashes are frozen before generating calibration and test observations in disjoint seed namespaces.

Calibration and static negatives contain eight equally weighted groups: the four individual nuisance families and the four multiple-source groups. Multiple-source components are generated independently for every trial and never reused across calibration/test or across test observations. Their relative levels are sampled within ±6 dB before final normalization. Component seeds, parameters and waveform hashes are retained. These negatives test multiple-source false alarms; they do not establish localization of a target accompanied by two independent interferers.

Continuous observations use one uninterrupted waveform realization per 24 s sequence. The target is absent during the first and last 2 s. Signed azimuth speed ranges from 6 to 18 degrees/s and reverses at the midpoint to -0.7 times its initial value; elevation varies sinusoidally from 15 to 65 degrees. The target level varies by ±3 dB. These are angular-motion stress cases rather than validated low-speed flight dynamics. The evaluation uses independent per-frame estimates without claiming an improved temporal tracker.

### B Comparisons and metrics

Raw localization compares PHAT, coherence-only weighting, harmonic-only weighting, their product, the candidate ranker without suppressed-beam descriptors, and complete SCCR. The four original estimators share their grid, phase convention, observations and preprocessing. The no-suppression ablation removes the 42 suppressed-spectrum features and three suppressed-to-ordinary ratios, leaving 104 features and the same fixed regression settings. Its training data and proposals remain identical.

For the weighted references, coherence contributes 0.05 + 0.95 gamma, while the harmonic mask uses the single largest fundamental score and a floor of 0.1. Their product defines the combined reference. The original detector multiplies the nonnegative best harmonic score by 0.25 plus mean harmonic-weighted coherence. These are fully specified reference implementations, not claimed exact reproductions of every published harmonic-SRP method.

Detection compares the original harmonic-coherence score, the learned spectral ablation and the full spectral-spatial detector. All receive the same calibration examples and strict order-statistic rule. Recall uses every positive trial; FPR uses every negative trial. Balanced accuracy is the mean of recall and specificity, independent of the 1:2 test class count. Single-source, multiple-source and individual-group FPRs are reported separately.

The principal direction error is

$$e=\operatorname{atan2}(\|\widehat{\mathbf{u}}\times\mathbf{u}\|_2,\widehat{\mathbf{u}}^T\mathbf{u}).$$ (16)

Angles are converted to degrees. Every positive observation contributes to unconditional mean, median, tail and 10-degree success statistics. Joint success requires both a detection and error no greater than 10 degrees, with all positive observations in the denominator. Rejected observations cannot silently improve that joint score.

Paired localization differences are computed on identical trials and bootstrapped within scene/SNR strata using 2000 resamples. Detection proportions use Wilson intervals; balanced accuracy uses independent stratified positive/negative resampling. Dynamic errors are averaged first within each sequence; uncertainty resamples complete sequences. These intervals condition on the frozen models, threshold and analytic generator. Multiple comparisons remain descriptive, without a multiplicity correction.

The workstation uses an Intel Core i7-12700KF and single-thread numerical-library settings. Timing measures complete per-frame feature extraction and prediction, excluding acquisition, synthesis, file I/O, initialization and display. The reported proposed-pipeline bound includes both full and spectral detector predictions, making it conservative for deployment of one detector. A 200 ms acquisition block remains separate from compute latency. Reference and proposed methods are implemented in Python rather than benchmarked on an embedded target.

## VI Results

### A Localization improvement and source association

{{LOCALIZATION_RESULTS}}

{{LOCALIZATION_TABLE}}

![Figure 2. Mean spherical localization error over all positive observations at each SNR. SCCR and its suppression ablation use the same candidate proposals and training partition.](../figures/improved_localization.png)

{{SCENE_RESULTS}}

{{SCENE_TABLE}}

### B Detection and multiple-source false alarms

{{DETECTION_RESULTS}}

{{DETECTION_TABLE}}

{{FPR_TABLE}}

![Figure 3. Independent-test detector ROC curves and separately calibrated operating points. The curves are descriptive; no threshold is selected from these test observations.](../figures/improved_roc.png)

### C Joint success, dynamic observations and computation

{{JOINT_RESULTS}}

{{DYNAMIC_RESULTS}}

{{COMPUTE_RESULTS}}

## VII Discussion

The proposed design addresses two distinct error mechanisms. Multiple proposals reduce premature commitment to the loudest or most periodic source. Candidate-conditioned spectra then ask which retained direction is consistent with target-associated acoustic structure. Interference suppression provides another description of a candidate, rather than replacing the raw observations with an assumed perfectly separated signal. The detector uses global evidence for presence, while the ranker assigns a direction; their different outputs are not interchangeable probabilities.

The results must also be interpreted in relation to supervision. SCCR learns from labelled development directions, whereas the PHAT references are analytic estimators. The improvement therefore includes information supplied by synthetic supervision and cannot be attributed solely to a more accurate delay formula. The spectral detector and no-suppression ranker provide narrower within-family ablations. No evaluated result establishes superiority to an independently trained neural system or reproduces another paper's field benchmark.

A remaining failure source is proposal recall. If every candidate follows the interferer or a spatial ambiguity, reranking cannot recover a missing target direction. Near-horizontal geometry, small source separation, errors in nominal channel calibration and finite harmonic resolution further limit association. The two-direction suppression model handles one competing steering vector. It should not be generalized to unrestricted source separation, and multiple-source negative detection is a different experiment from target localization among multiple interferers.

The generator still defines the class semantics. Even after adding multiple-source negatives and eliminating absolute-amplitude cues, a classifier may exploit spectral or modulation differences specific to the generator. Different random seeds establish independent realizations, not new aircraft types, source models or recording sessions in the physical world. The experiment omits measured microphone responses, nonlinear wind buffeting, realistic ground reflection, calibrated radiation and absorption, exact retarded-time propagation and validated Doppler dynamics. Consequently, the proposed mechanism and measured gains warrant field testing rather than direct claims about operational range or unrestricted UAV identity.

A field study should use labelled flights and difficult mechanical backgrounds separated by recording session, verify geometry and channel delays, and freeze thresholds before the test flights. Actual multi-interferer positives would determine whether candidate association remains useful when more than one distractor must be suppressed. The implementation's stored proposals, scores, validity decisions and per-observation outputs make both successful associations and remaining failures inspectable.

## VIII Conclusion

{{CONCLUSION}}

## Data and Code Availability

The supplementary package contains complete development and test multichannel observations, constituent provenance for negative mixtures, fitted detector and candidate models, source hashes, fixed partitions, per-frame estimates and reproduction scripts. A separately archived real recording from Yang and Bitzer [19] retains its CC BY 4.0 attribution and is not included in the quantitative evaluation. Independent checks verify amplitude invariance, candidate/beam conventions, recording-level fold separation, cache/model consistency and test-input separation.
