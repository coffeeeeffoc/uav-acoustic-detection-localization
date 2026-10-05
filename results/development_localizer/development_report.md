# Frozen multi-hypothesis acoustic localizer: development record

## Evidence boundary and callable contract

The original full/test partition is now explicitly DEVELOPMENT data. This study used its 1,000 positive and 1,000 negative recordings. No newly generated acoustic seed, future calibration recording or fresh test recording entered candidate generation, fitting, selection or evaluation. Old results, recordings, experiment.py and manuscripts were not edited.

    from improved_localizer import ImprovedLocalizer
    main = ImprovedLocalizer()
    ablation = ImprovedLocalizer(
        model_path="results/development_localizer/candidate_ranker_no_null_model.npz")
    result = main.analyze(audio)  # finite (1600, 8) NumPy array, 8000 Hz
    azimuth, elevation = result["az_hat"], result["el_hat"]

Default weights: results/development_localizer/candidate_ranker_model.npz.
Ablation weights: results/development_localizer/candidate_ranker_no_null_model.npz.
The default class resolves its model relative to the workspace, independent of the caller's working directory. An explicitly supplied relative model_path follows the caller's working directory.

Inference accepts AUDIO ONLY. There is no scene, nominal SNR, seed, true f0, true direction or source identity argument. Score is an uncalibrated source-candidate ranking score, not a UAV detection probability. The parent detector must decide presence; this unconditional localizer can produce a direction even on silence/negative audio. Its processing_ms is measured around feature extraction, proposals, ranking and output construction; initialization/model loading are excluded. return_map=True adds five proposal maps and a sparse ranking map: unscored grid locations are NaN, candidate locations carry ranker scores. map_kind explicitly identifies sparse_candidate_ranking. Do not label the dense PHAT proposal map as the learned final acoustic map.

## Actual development progression

The root issue was source identity. Coherent broadband and engine-like harmonic interferers could capture the strongest PHAT or harmonic peak. Reliability weighting alone does not establish which source is the target.

Round 1 compared six fixed alternatives to the original PHAT. Let P be mean-channel Welch power, A=|G|, R=A/median(A over retained bins and all microphone pairs), e=max(P/median_11(P)-1,0), S=.05+.95 e/(1+e), and C=sqrt(.1+.9 MSC). The variants were:

- beta_0p75: weight R^.25.
- beta_0p5: weight R^.5.
- excess_soft: weight S.
- coherence_excess: weight SC.
- pair_excess: replace e by pairwise max(A/median_11(A)-1,0), soft-saturate with the same .05/.95 constants, then multiply by C.
- beta_excess: weight S clip(sqrt(R),.2,5).

All used the original 512-sample Welch phase spectrum, five Hann windows, 256-sample hop, 200–3000 Hz band, 28 microphone pairs, 3601-direction upper-hemisphere grid and 8x inverse-FFT lag interpolation.

Round 2 added four controls using a 1600-point full-frame Hann FFT and pairwise phase. Let e_F=max(P_F/median_31(P_F)-1,0), h=e_F/(1+e_F). full_phat uses weight 1; full_excess uses .005+.995h; full_coherence_excess multiplies that weight by C interpolated from the short-window frequencies; full_peak_excess uses (.005+.995h^2)C. The same physical frame, spatial grid and 8x lag interpolation are retained.

None of these ten alternatives improved BOTH overall mean spherical error and within-10-degree rate over the original PHAT. The best short-window mean was 24.771088 degrees versus PHAT 24.840781, while within10 declined from .664 to .658. The full-frame trials also failed the joint criterion. Their raw results and exact source snapshots remain under round1/, round2/, variant_frames.csv and variant_summary.csv. They are not erased or presented as successful variants.

The last stage introduced one fixed candidate-ranker configuration. It used no hyperparameter sweep and no per-scene/SNR rule. The requested no_null model is a feature-attribution ablation with the same constants, candidates, labels, folds and center-selection procedure; it is not another search over hyperparameters.

## Candidate generation and two-source beam evidence

Directions use the unchanged illustrative array, azimuth counterclockwise from +x and elevation above the plane. The nominal sound speed is 343 m/s. The grid has azimuth 0:3:357 degrees, elevation 0:3:87 degrees, plus one zenith. There are 3601 points. An upper-hemisphere prior is required for this planar array.

1. Compute the original short-window PHAT map and the full_excess map defined above.
2. Compute an additional 2048-point FFT of the full 1600-sample periodic-Hann frame. Demean each channel and normalize by global RMS before candidate spectral feature extraction. Average channel powers into P. Define L=GaussianSmooth_1bin[log(1+P/max(median_31(P),1e-15))-log2]. Median padding is nearest; Gaussian padding is SciPy's default reflect. Search bases b=80,82,...,240 Hz using

   J(b) = sum_(k=1..12) k^(-1/2) L[round(k b 2048/8000)] / sum_(k=1..12) k^(-1/2).

   Sort these scores descending and greedily retain three bases separated by at least 20 Hz. They are competing mixture hypotheses, not true target bases.
3. For each base, form a short-window harmonic PHAT proposal map with

   H_b(f) = .02 + .98 exp[-d_b(f)^2 / (2 max(8,.012 f)^2)],
   d_b(f) = |f-round(f/b)b|,

   inside 200–3000 Hz and zero outside. The score sums PHAT pair correlations at nominal geometric delays. This yields five proposal maps: plain PHAT, full_excess, and three harmonic maps.
4. Greedily take three peaks from plain PHAT and two from each other map. After each peak, suppress grid directions at spherical distance <=20 degrees within that map. Across maps, discard a candidate within <=7 degrees of an earlier retained direction. At most 11 candidates remain. The raw PHAT maximum is always the first retained candidate. No truth-nearest candidate is inserted. Candidate counts and indices are saved.
5. For a candidate u define tau_um=-p_m dot u/343, alignment q_um(f)=exp(j2 pi f tau_um), and delay-and-sum beam

   B_u(f) = (1/8) sum_m q_um(f) X_m(f).

   Among the retained directions strictly more than 15 degrees away, choose v with greatest plain-PHAT proposal response. Define

   r_uv(f) = (1/8) sum_m q_um(f) conj(q_vm(f)),
   Z_u(f) = [B_u(f)-r_uv(f)B_v(f)] / max(1-|r_uv(f)|^2,.1).

   Z is a regularized two-source constrained beam, used to obtain evidence about candidate source identity. The .1 floor prevents nearly collinear low-frequency steering vectors from amplifying the denominator arbitrarily. This assumes two dominant directions; it is not a validated general multi-source separator.

## Exact feature layout

All features are derived from observed audio and proposal maps. No absolute azimuth/elevation coordinate feature is supplied.

| Indices (zero-based) | Dimension | Content |
|---|---:|---|
| 0:42 | 42 | Mixture spectrum |
| 42:84 | 42 | Candidate ordinary beam spectrum |
| 84:126 | 42 | Candidate interference-cleaned beam spectrum |
| 126:130 | 4 | 200–800 Hz directional capture quantiles and log cleaned/ordinary power |
| 130:134 | 4 | 800–1600 Hz equivalent |
| 134:138 | 4 | 1600–3000 Hz equivalent |
| 138:143 | 5 | Raw proposal map responses at the candidate |
| 143:148 | 5 | Responses divided by each proposal map's maximum (floor 1e-15) |
| 148 | 1 | Nearest other retained candidate's spherical angular separation |

Each 42-dimensional spectrum descriptor first normalizes its power over all FFT bins. In each of five bands (80–3000, 80–400, 400–1000, 1000–2000, 2000–3000 Hz), it computes seven values: log band power fraction, spectral flatness, entropy normalized by log bin count, local-median log-contrast quantiles .5/.9/.99 and contrast SD. This gives 35 features. Four further values summarize the same weighted harmonic comb: maximum, maximum at a base >=20 Hz from the first, mean and SD. The last three features give the 200–3000 Hz power fraction within 5, 10 and 20 Hz of a nearest harmonic of the best spectrum-specific base.

Directional capture uses .25/.5/.9 quantiles of |B_u|^2 divided by mean-channel power. The fourth value per band is log(sum|Z_u|^2 / sum|B_u|^2), with 1e-15 added to each band sum.

The no_null ablation drops exactly 84:126 plus 129,133,137. Thus it retains 104 of the 149 raw features: mixture and ordinary-beam descriptors, nine capture quantiles, ten map values and the separation. Both models accept the same raw 149-feature matrix; predict selects saved feature_indices. The no_null call still computes all features for a simple common implementation, so its runtime is not a benchmark of an optimized null-free front end.

## Fitting objective and folds

For positive-frame candidate c with spherical error theta_c, define y_c=exp[-(theta_c/10 degrees)^2]. All negative-frame candidates have y=0. Truth is used only after audio-only proposals and features have been computed. Candidates with y>=exp(-1) form the near-target group; all others form the other group.

For each training split, standardize each selected feature using its training mean and SD floored at .05. Clip standardized values to [-8,8]. Using model seed 90210, select up to 128 near-target and 128 other candidate rows as Gaussian-basis centers. Let D be 149 or 104 and width=1:

   K(x,c_j)=exp[-||z(x)-z(c_j)||^2/(2 D width^2)].

Append a constant intercept column to K. Near-target rows have weight n_other/n_near; other rows have weight 1. Fit

   a = argmin_a sum_i w_i (Ktilde_i a-y_i)^2 + .1 ||a||^2,
   a = (Ktilde^T W Ktilde + .1 I)^(-1) Ktilde^T W y.

The intercept is also regularized. The score is K(x,C)a_without_intercept+a_intercept. At inference, select the candidate with highest score. Width=1, ridge=.1, center count and weighting were fixed; there was one learned-model configuration plus the requested no-null attribution ablation.

Internal evaluation assigns whole trials to five folds, independently shuffling positive and negative trial indices with model seed 90210, then assigning shuffled indices cyclically across folds. Every candidate from one recording stays in one fold. Each fit learns scaler, centers and coefficients without its validation fold. Primary development metrics use positive out-of-fold predictions. The shipped models are then refit on all 2,000 OLD trials. Their resubstitution results are saved separately and must not be substituted for the grouped-fold numbers.

Because this procedure was designed after reviewing old-data failures, grouped OOF is still development evidence, not restored blind testing. Frozen-model evaluation on fresh independent data is the parent's next step. Parent detector hard negatives and fresh calibration/test data did not enter these localizer fits.

## Runtime, reproducibility and attribution limits

The finalization command replays 40 prespecified old -5dB frames (ten per scene) for EACH model. Coordinates and scores must match cached-feature inference; four cases also verify the raw PHAT first candidate against Engine. Timing surrounds the public analyze call. Model/grid initialization, warm-up, NPZ input, and the 200 ms acquisition interval are excluded. Four timing calls include optional sparse diagnostics. The host is the previously recorded i7-12700KF workstation; library thread requests are one. This is not organizer-device certification.

The feature digest covers ImprovedLocalizer.__init__, Engine.__init__, candidates, spectral_features, _spectra, _localize, and JSON ARRAY/FS/N/C0 constants. Cached candidate data validates both this digest and the digest of the sorted old input NPZ names/content hashes, including order. Both model files carry feature/source/input-archive hashes. Loading checks feature implementation and complete current localizer source hash. The regenerated guarded cache is checked against the earlier cache for bit-identical feature values; default 149-dimensional fitted coefficients are checked against the pre-ablation model.

The contribution should be described as a specific, reproducible proposal-and-ranking combination and its validated behavior. PHAT/SRP, multiple hypotheses, beamforming/null constraints, spectral descriptors and Gaussian ridge learning are established components, not inventions claimed here. A lower development error does not by itself demonstrate a new general source-identification principle, real-drone reliability or range. The no_null comparison must determine whether the cleaned-beam features add measurable value; if it does not improve, the nuller cannot be credited with improvement. Candidate availability, unresolved nearby sources, the two-source approximation, generator-specific engine/rotor signatures, planar elevation conditioning, and selection optimism remain explicit limitations.

## Executed numerical results

The following tables are appended from actual saved grouped-fold predictions and runtime checks after the final freeze. Any nearest-candidate oracle is a truth-based diagnostic bound only, never the selection rule or a reported deployable algorithm.

All errors below are degrees. Within10 is the fraction with spherical error <=10 degrees, evaluated without detection gating. Each overall result uses the same 1,000 positive old-development trials. Full-precision rows remain in the CSV/JSON artifacts.

### Overall controls and final grouped OOF models

| Method | Mean | Median | P95 | Within10 (%) | Azimuth MAE | Elevation MAE |
|---|---:|---:|---:|---:|---:|---:|
| phat | 24.841 | 2.774 | 114.256 | 66.4 | 28.967 | 8.857 |
| beta_0p75 | 25.320 | 2.838 | 110.992 | 66.0 | 29.649 | 9.077 |
| beta_0p5 | 26.110 | 2.959 | 114.256 | 64.8 | 30.716 | 9.257 |
| excess_soft | 25.099 | 3.010 | 110.852 | 65.4 | 28.843 | 9.151 |
| coherence_excess | 24.771 | 2.956 | 110.852 | 65.8 | 28.443 | 8.919 |
| pair_excess | 25.485 | 3.114 | 110.618 | 64.9 | 29.375 | 9.322 |
| beta_excess | 24.964 | 2.967 | 113.444 | 65.3 | 28.869 | 8.813 |
| full_phat | 25.081 | 2.971 | 114.957 | 65.8 | 29.134 | 8.927 |
| full_excess | 24.980 | 3.069 | 110.618 | 64.8 | 28.807 | 9.104 |
| full_coherence_excess | 25.421 | 3.270 | 110.618 | 64.7 | 29.638 | 9.158 |
| full_peak_excess | 25.348 | 3.346 | 110.852 | 64.5 | 29.130 | 9.351 |
| candidate_ranker_full_oof | 17.632 | 2.517 | 94.998 | 74.7 | 19.413 | 7.073 |
| candidate_ranker_no_null_oof | 18.904 | 2.531 | 97.349 | 73.2 | 21.146 | 7.490 |

The full149 model reduces mean error by 7.209 degrees versus PHAT (conditional paired 95% interval 5.966 to 8.493) and raises within10 by 8.3 percentage points (6.8 to 9.9). The no_null104 model reduces mean error by 5.937 degrees (4.654 to 7.221) and raises within10 by 6.8 points (5.4 to 8.3). Intervals use 2,000 independent-trial resamples within the 20 scene/SNR cells, resampling paired fixed predictions with seed 90210. They do not account for fitting or development selection; shared training folds also prevent interpreting these as independent model-retraining uncertainty.

The direct cleaned-feature attribution comparison is full149 versus no_null104: mean error reduction 1.272 degrees (conditional 95% interval 0.552 to 2.018), within10 gain 1.5 percentage points (0.5 to 2.5). Full149 improves 55 trials, worsens 25 and leaves 920 unchanged. These development results suggest an incremental contribution of the cleaned features, pending the independently frozen comparison; they are not evidence that every scene benefits.

The truth-selected nearest available candidate would have mean error 13.220 degrees and within10 80.3%. This is an unavailable oracle diagnostic. It shows that 19.7% of positive frames have no proposal within 10 degrees, which the current ranker cannot repair. The actual full149 OOF P95 remains 94.998 degrees; directional interference still has mean error 42.032 degrees and within10 only 37.6%.

### All scene, SNR and scene-by-SNR groups

Every scene/SNR cell has 50 independent positive trials; scene totals have 250 and SNR totals 200. Positive last-column values favor full149 over PHAT; negative values expose deterioration. Each Mean / hit entry is degrees / percent within10.

| Group | n | PHAT mean / hit | No-null104 mean / hit | Full149 mean / hit | PHAT minus full mean |
|---|---:|---:|---:|---:|---:|
| sensor_noise | 250 | 5.539 / 89.2 | 5.174 / 90.0 | 4.679 / 89.6 | +0.860 |
| wind | 250 | 1.916 / 100.0 | 1.916 / 100.0 | 1.916 / 100.0 | +0.000 |
| directional | 250 | 54.503 / 22.4 | 46.464 / 31.2 | 42.032 / 37.6 | +12.471 |
| engine | 250 | 37.405 / 54.0 | 22.062 / 71.6 | 21.900 / 71.6 | +15.505 |
| snr=-15 | 200 | 38.683 / 39.5 | 38.342 / 42.0 | 36.716 / 42.5 | +1.967 |
| snr=-10 | 200 | 39.990 / 48.5 | 26.627 / 64.5 | 26.822 / 63.5 | +13.168 |
| snr=-5 | 200 | 25.778 / 68.0 | 16.159 / 77.0 | 14.666 / 79.0 | +11.113 |
| snr=0 | 200 | 17.808 / 76.5 | 10.708 / 84.0 | 7.575 / 89.0 | +10.232 |
| snr=5 | 200 | 1.945 / 99.5 | 2.684 / 98.5 | 2.380 / 99.5 | -0.435 |
| sensor_noise:-15 | 50 | 17.313 / 54.0 | 14.392 / 58.0 | 12.363 / 58.0 | +4.950 |
| sensor_noise:-10 | 50 | 4.155 / 92.0 | 4.293 / 94.0 | 4.722 / 90.0 | -0.567 |
| sensor_noise:-5 | 50 | 2.192 / 100.0 | 2.192 / 100.0 | 2.192 / 100.0 | +0.000 |
| sensor_noise:0 | 50 | 1.916 / 100.0 | 1.916 / 100.0 | 2.002 / 100.0 | -0.085 |
| sensor_noise:5 | 50 | 2.119 / 100.0 | 3.076 / 98.0 | 2.119 / 100.0 | +0.000 |
| wind:-15 | 50 | 2.115 / 100.0 | 2.115 / 100.0 | 2.115 / 100.0 | +0.000 |
| wind:-10 | 50 | 2.102 / 100.0 | 2.102 / 100.0 | 2.102 / 100.0 | +0.000 |
| wind:-5 | 50 | 1.929 / 100.0 | 1.929 / 100.0 | 1.929 / 100.0 | +0.000 |
| wind:0 | 50 | 1.648 / 100.0 | 1.648 / 100.0 | 1.648 / 100.0 | +0.000 |
| wind:5 | 50 | 1.785 / 100.0 | 1.785 / 100.0 | 1.785 / 100.0 | +0.000 |
| directional:-15 | 50 | 65.274 / 2.0 | 68.276 / 2.0 | 65.701 / 4.0 | -0.427 |
| directional:-10 | 50 | 73.924 / 0.0 | 70.127 / 4.0 | 67.423 / 6.0 | +6.500 |
| directional:-5 | 50 | 65.284 / 4.0 | 53.907 / 14.0 | 49.901 / 20.0 | +15.382 |
| directional:0 | 50 | 65.682 / 8.0 | 35.659 / 40.0 | 23.043 / 60.0 | +42.638 |
| directional:5 | 50 | 2.353 / 98.0 | 4.353 / 96.0 | 4.093 / 98.0 | -1.740 |
| engine:-15 | 50 | 70.030 / 2.0 | 68.583 / 8.0 | 66.686 / 8.0 | +3.344 |
| engine:-10 | 50 | 79.779 / 2.0 | 29.985 / 60.0 | 33.042 / 58.0 | +46.737 |
| engine:-5 | 50 | 33.710 / 68.0 | 6.608 / 94.0 | 4.641 / 96.0 | +29.069 |
| engine:0 | 50 | 1.984 / 98.0 | 3.608 / 96.0 | 3.608 / 96.0 | -1.624 |
| engine:5 | 50 | 1.523 / 100.0 | 1.523 / 100.0 | 1.523 / 100.0 | +0.000 |

Full149 worsens mean error relative to PHAT in these cells: sensor_noise:-10 by 0.567 degrees; sensor_noise:0 by 0.085 degrees; directional:-15 by 0.427 degrees; directional:5 by 1.740 degrees; engine:0 by 1.624 degrees. Wind outputs are unchanged. At 5 dB overall the mean worsens by 0.435 degrees with the same 99.5% within10 rate. These failures are retained rather than hidden by the overall gain.

### Shipped model diagnostics and runtime

| Shipped all-old-data model | Features | Resubstitution mean | Resubstitution within10 (%) | 40-frame median ms | 40-frame P95 ms |
|---|---:|---:|---:|---:|---:|
| full | 149 | 16.464 | 75.6 | 21.248 | 23.784 |
| no_null | 104 | 18.469 | 73.4 | 19.100 | 21.808 |

These resubstitution numbers are diagnostics only. The primary reported evidence remains grouped OOF. Processing time is elapsed perf_counter time around computation, not accumulated operating-system process CPU time. The unchanged front end computes all 149 raw features for both models. Each number excludes setup/model loading, warm-up, NPZ I/O and the 200 ms acquisition window. Runtime probes are fixed old -5 dB recordings, not new statistical trials.

### Frozen files and verification

The candidate cache contains 8,750 rows x 149 raw features from exactly 2,000 old trials. The guarded full rebuild produced bit-identical features to the earlier cache. Saved OOF candidate scores, per-trial fold membership, per-positive winner rows, all-training models, input filename/content hashes and representative sparse/proposal maps are retained. Eighty public audio-only replay calls matched cached inference; raw PHAT retention, amplitude scaling, silence, shape rejection and exact no-null mask passed. See verification.json. The earlier development_protocol.json and development_summary.json describe scalar screening history; frozen_config.json and frozen_development_summary.json define this final freeze.

Frozen source SHA256: 6edd9b9b46f13bf5c601711827083f0a8a0aa8c4204916ffd458187e0c978f95.
Full149 model SHA256: 6338fad6611cc7b411387eb926cc3e7f9c981af434ce04f68b778e1f22524eed.
No-null104 model SHA256: c311f34098767523df7a04eb26625e02e06e0c467c8759312e2562adf4d0536b.
Candidate feature SHA256: 290328899f2de68e098962d97217092773792c7e78c4c508fd9105ea4a22cbcc.
Old input archive SHA256: c21a6b97f0fadf5324adff68c814ee27c2a38ee492460a5f2598c7cefa733c8c.

artifact_manifest.json records localizer source, unchanged Engine dependency, and all development artifacts (excluding the manifest itself). The source and models are fixed before any fresh evaluation. The parent owns results/improved for subsequent independent results; none of those results is incorporated into this development report.
