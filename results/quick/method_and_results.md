# Exact method and results: simulation-only acoustic detection and direction estimation

This file is generated from executed CSV records. Run mode: **quick**. Master seed: **20261002**. No organizer data, measured array, calibrated source levels, actual-flight localization labels, or target-device benchmark are used. The model's 20–80 m distance is solely a geometric curvature parameter: prescribed SNR is normalized independently of range. Neither 100 m detection nor a maximum effective range is established. No result from `data/public` is included here. This is an interpretable combination/ablation study, not a priority claim for SRP, PHAT, harmonic selection, coherence, or smoothing.

## Frozen experiment and independent units

80 validation negatives; 40 test negatives; 60 test positives. Positives are balanced across SNR = -15, -10, -5, 0, +5 dB and four nuisance scenes. Every static trial has fresh source, noise, direction, sound speed, source phases and gains. SNR cells do not recycle the same waveform. The four algorithms are paired on the same trial. 12 independent continuous sequences last 8 s each. Tracking is balanced across four scenes and nominal SNR -10, -5, 0 dB. There are 12 new sensitivity trials, each evaluated under four paired conditions. Quick mode is an engineering smoke check and is not combined with full mode. Parameters were fixed before the full run; there is no test-driven parameter search.

SeedSequence entropy is `[20261002, split, scene_index, ...]`; exact per-trial lists are stored in NPZ metadata, CSV and `data/synthetic/quick/manifest.jsonl`. Split codes are 1 validation negatives, 2 test negatives, 3 test positives, 4 sensitivity, 5 tracking, 6 bootstrap, 77 sensor perturbations, 90 self-test. Static positive suffixes are `[snr_index, trial_index]`; static negative suffixes are `[trial_index]`; tracking/sensitivity suffixes are `[snr_index, repeat_index]`. Scene families are shared between calibration and test but realized physical scenes are independent; this is not a held-out-environment or held-out-drone experiment.

## Coordinate and synthesis model

Azimuth increases counterclockwise from +x; elevation is above the array plane. $u(a,e)=(\cos e\cos a,\cos e\sin a,\sin e)$. Eight microphones use the exact coordinates in `config.json`; diameter is 0.394671 m. The array is planar, so an upper-hemisphere prior is essential; it cannot resolve the lower/upper mirror ambiguity. The search includes a single zenith point and full azimuth coverage. Zenith azimuth is intrinsically undefined; spherical error is the principal metric and raw wrapped azimuth errors are also disclosed. True static directions are uniform in azimuth and in sine elevation (uniform solid angle on the upper hemisphere).

A source waveform is synthesized at 24 kHz, then evaluated at fractional arrival times by linear interpolation to 8 kHz. For microphone $m$, $x_m(t)=g_m[d_m(t)+r_m(t)+n_m(t)]$ conceptually, with each contribution's normalization implemented explicitly in `simulate`. Direct source delay is $\tau_m(t)=(\|R(t)u(t)-p_m^{actual}\|-R(t))/c+\delta_m$. Propagation uses spherical distances and relative amplitude $R/\|Ru-p_m\|$. Actual sound speed is uniform 338–348 m/s; steering assumes 343 m/s. Per-channel gains are log-normal with Gaussian 0.6 dB standard deviation. Nominal geometry/delay perturbations are zero; sensitivity adds Gaussian xyz offsets (including z) and Gaussian fixed channel time offsets. Different generation and steering models reduce the most direct inverse crime, but do not establish real-world validity.

The multirotor-like signal sums four oscillators. A nominal base is uniform 85–230 Hz. Each rotor has a Gaussian relative offset SD 0.012 and sinusoidal frequency modulation of relative depth uniform 0.008–0.025, rate 0.6–2 Hz and random phase. Harmonic phases are independent; amplitudes are uniform(0.6,1.4)/$k^{0.65}$, for $k=1,\ldots,\min(15,\lfloor3200/(1.07f_0)\rfloor)$. Unit-RMS tonal and 120–3200 Hz third-order Butterworth-filtered Gaussian broadband parts have nominal tonal power fraction uniform 0.55–0.85 before their combination and final normalization. A sinusoidal amplitude envelope has depth 0.12 and frequency 0.3–1.5 Hz. This phenomenological model is not a validated aircraft sound-emission model.

A weak echo has RMS ratio uniform 0.05–0.25 relative to the direct target, delay 3–12 ms, azimuth offset 25–80 degrees and elevation max(5 degrees,0.65 times target elevation). It is a synthetic secondary path, not a physically ray-traced outdoor ground reflection. The target direct-path mean-square power across all microphones divided by total nuisance power defines SNR; the echo is excluded from the SNR numerator and nuisance denominator. Exact achieved per-frame SNR is saved. There is no source-level calibration, atmospheric absorption model, exact retarded-time solution, moving-source Doppler validation, or distance-to-SNR conversion.

Nuisance scenes: (1) independent unit Gaussian sensor noise; (2) 0.35 times sensor noise plus independent 180 Hz second-order low-pass noise per channel, plus 0.25 times a shared 90 Hz low-pass component, normalized before mixing; (3) 0.6 times sensor noise plus a directional 160–3200 Hz third-order band-pass noise source; (4) 0.6 times sensor noise plus a directional one-oscillator engine-like harmonic confounder. Engine base/offset distributions overlap the target; its modulation depth is 0.001–0.004 and harmonic fraction 0.82–0.95. Nuisance direction is uniform azimuth and elevation 0–65 degrees; range is uniform 10–60 m. No minimum target/interferer angular separation is imposed. The wind model is colored correlated noise, not measured atmospheric turbulence. Engine negatives are deliberately difficult: harmonicity and spatial coherence do not identify drone class.

## Spectral front end, estimated base and detector

Frames are disjoint 1600-sample (0.2 s) blocks at 8 kHz: output cadence 5 Hz. Each channel is demeaned over the frame. Five 512-point periodic-Hann segments, hop 256, start at samples 0,256,512,768,1024; the remaining 64 samples enter the full-frame harmonic estimator but not the Welch estimate. For pair $i<j$, $G_{ij}(f)=\frac15\sum_\ell X_{i\ell}(f)X_{j\ell}^*(f)$ and $P_i(f)=\frac15\sum_\ell|X_{i\ell}(f)|^2$. Define $\gamma_{ij}^2=\mathrm{clip}(|G_{ij}|^2/(P_iP_j+10^{-20}),0,1)$ and $Q_{ij}=G_{ij}/\max(|G_{ij}|,10^{-20})$. This is a finite-sample Welch magnitude-squared coherence estimate; overlap reduces effective sample count and no unbiased-coherence claim is made. It is not computed from a single snapshot, which would give trivial coherence.

An additional 2048-point real FFT of the entire periodic-Hann-windowed frame is used for harmonic evidence; zero-padding interpolates spectral samples but does not improve the physical 5 Hz window resolution. Average the eight channel powers into $P(f)$. Let $M(f)$ be a 31-bin local median, nearest-edge padding, and $L(f)=\log(1+P(f)/\max(M(f),10^{-20}))-\log2$. Smooth $L$ with a Gaussian of SD one FFT bin (SciPy default reflect edges). For $b\in\{80,82,\ldots,240\}$ Hz, evaluate $J(b)=\sum_{k=1}^{12}k^{-1/2}L(\operatorname{round}(kb\cdot2048/8000))/\sum_{k=1}^{12}k^{-1/2}$. The argument denotes a nearest FFT-bin index, not interpolation. $\hat f_0=\arg\max_b J(b)$; ties use the first candidate. There is no true-base input. Absolute percentage error against the generator's nominal base is a diagnostic only: median 1.2766% across all positive test trials. Four perturbed rotors do not possess one exact common instantaneous base.

Within the 200–3000 Hz band, $d(f)=|f-\operatorname{round}(f/\hat f_0)\hat f_0|$, $\sigma(f)=\max(8,0.012f)$ Hz, and $H(f)=0.1+0.9\exp[-d(f)^2/(2\sigma(f)^2)]$. $H=0$ outside the band. On the 512-point FFT grid the retained bins actually run from 203.125 to 3000 Hz. The floor retains broadband evidence. Detection score is $D=\max(0,J(\hat f_0))[0.25+\sum_{i<j,f}H(f)\gamma_{ij}^2(f)/(28\sum_fH(f))]$. One common detector is used for all four localizers: detection results must not be presented as four different trained detectors.

Only independent validation-negative scores set the threshold. Sort $n=80$ scores, take order statistic $k=\lceil(n+1)(1-0.05)\rceil=77$ (1-based), and declare detection iff $D>\theta$. The fitted threshold is **1.74849167423**, validation empirical FPR **0.037500**. Equal-scene stratification targets this explicit nuisance mixture. The order-statistic rule is inspired by finite-sample calibration, but stratified non-identical draws mean no universal distribution-free or per-scene 5% guarantee is asserted. There is no positive-label fitting, test-threshold adjustment or double-threshold hysteresis. Engine-specific false alarms may exceed 5% even when aggregate FPR does not.

## Four paired localization ablations

Nominal predicted pair delay is $\tau_{ij}(u)=-(p_i-p_j)^Tu/343$. The common objective is

$$S_w(u)=\sum_{i<j}\sum_{f\in B} w_{ij}(f)\Re\{Q_{ij}(f)e^{j2\pi f\tau_{ij}(u)}\}.$$

Weights are PHAT: $w=1$; coherence: $w=C_{ij}=0.05+0.95\gamma_{ij}^2$; harmonic: $w=H$; combined: $w=C_{ij}H$. Frequency bins outside B are zero. Implementation takes a 4096-point inverse real FFT (8x interpolation), evaluates pair correlations with linear lag interpolation and sums all 28 pairs. The search is 3-degree azimuth 0–357 and elevation 0–87, plus one zenith, totaling 3601 directions. No local refinement or test-selected grid is used. Peak values are normalized by total weight; multiplying a method's whole map by a positive scalar does not affect argmax. Detector/f0 data are shared but scoring truth is not passed into `Engine.analyze(audio)`.

## Causal tracking and latency

Continuous sequences have a target absent during the first and last 2 s (20 ms boundary ramps); it is present in between. The same continuous waveform, nuisance, gains, geometry and sound speed are used throughout a sequence. Target azimuth starts uniform 0–360, moves with signed speed uniform 6–18 deg/s and reverses at half the sequence duration to -0.7 times the original speed. Elevation is $40+25\sin(2\pi t/T+\phi)$ degrees, range is $R_0+1.5\sin(2\pi t/T)$ m, and target level varies by $3\sin(2\pi t/T)$ dB. These are angular-maneuver stress trajectories, not validated low-speed flight kinematics: azimuth motion alone can imply approximately 25 m/s at the largest modeled radius and angular rate; elevation motion adds velocity and the abrupt turn has no acceleration constraint. The trajectory is evaluated at each frame center. Subframe motion therefore differs from the estimator's constant-within-frame steering assumption. Labels/trajectory never initialize or update a tracker.

For each localizer independently, raw estimates and two causal smoothers are saved. An accepted unit-vector observation $u_t$ gives $z_t=\mathrm{normalize}(0.65z_{t-1}+0.35u_t)$; the first accepted observation initializes state. `smooth_all` accepts every frame, including absence. `gated` accepts only detections; it holds the last state for at most 5 consecutive misses (1.0 s), invalidates on miss 6, and restarts on the next detection. `detected`, `valid`, `stale` and `consecutive_missed_detections` are stored separately. A held direction is not a new detection. Missing output is retained as unavailable, never discarded from coverage/success denominators. No future observation, centered smoothing, true direction, prelabelled target start or fitted trajectory is used.

This fixed smoother trades noise reduction for maneuver lag. The 1 s hold rule can violate the competition's 0.5 s interruption requirement and can retain false directions. Accordingly coverage, absent-period output rate, raw/smoothed mean error, per-sequence p95 error, error within one second of the turn, movement-step RMS and chord-velocity residual are all retained. Chord-velocity residual is $(180/\pi)\|(\hat u_t-\hat u_{t-1})-(u_t-u_{t-1})\|/0.2$; its sequence RMS is reported only on adjacent available positive frames and is not an exact spherical angular velocity. Detection continuity is scored separately from held-output continuity. The fraction of contiguous 25-positive-frame windows with detection recall at least 0.8 and no miss run over 0.5 s is an illustrative simulation check, not a range result. Overlapping windows are descriptive and never bootstrap units.

## Metrics and uncertainty

TPR = TP/Npositive, FPR = FP/Nnegative, balanced accuracy = (TPR + 1 - FPR)/2. For each SNR, the same complete negative test set is used; it is not resampled audio or an SNR-conditioned negative set. Spherical error is $\operatorname{atan2}(\|\hat u\times u\|,\hat u^Tu)$ in degrees. Signed azimuth error is $(\hat a-a+180)\bmod360-180$, elevation error is $\hat e-e$. Report mean/median/RMSE/p90/p95, absolute coordinate errors, unconditional fraction within 10 degrees, detected-only error and denominator, and joint (detected AND error at most 10 degrees)/all positives. Conditional localization errors must not be used as unconditional success rates. These are explicitly defined research metrics, not the organizer's unspecified official combined-angle score.

For static data, 2000 bootstrap replicates independently sample whole trials with replacement within scene x SNR strata (within scene for negatives), preserving the designed mix. A method difference is paired before resampling: PHAT error minus alternative error. Positive paired values mean improvement. Detection-rate intervals use Wilson binomial intervals; balanced-accuracy intervals independently resample positive and negative strata. Intervals are descriptive Monte Carlo uncertainty under this generator, not uncertainty over all real drone/environment populations; there is no multiplicity correction. Sensitivity paired increases use condition error minus nominal error, so positive is worse. All sensitivity changes reuse exactly the same source and noise random draws; only a separate standard-normal sensor perturbation stream is scaled.

Tracking summary values are equal-weight means of per-sequence metrics, with 2000 whole-sequence bootstrap samples for means and paired raw-minus-smoothed errors. Frames, STFT windows and overlapping detection windows are never bootstrap units. Fewer than two independent units provide no informative bootstrap interval: `bootstrap_mean` returns `[None, None]` (JSON `[null, null]`), including a one-sequence quick gated subset. Gated conditional-error averages use only sequences with available output; their counts and coverage are explicitly reported, and no favorable comparison is inferred from dropping unavailable sequences. In this run the combined gate produces any positive-period output in only 1 of 12 sequences. Any available conditional bootstrap interval is weak evidence about this selected subset and is not generalized to missed sequences or real flight populations. The `p95_deg` tracking aggregate is the mean of within-sequence p95s, not a pooled p95. First-detection latency is measured at the end of the first positive detected frame relative to target onset; sequences never detected are counted and omitted only from the conditional latency average.

## Observed primary outcomes and limits

Test recall is **0.050000**, false-alarm rate **0.100000**, and balanced accuracy **0.475000**. Descriptive test ROC AUC is **0.736667** (no AUC CI is claimed); equal-score groups enter the curve together and trapezoidal integration handles ties. ROC thresholds use inclusive score comparisons, and the independently frozen strict-threshold operating point is separately marked. The ROC is descriptive only and selects no deployment threshold. Unconditional mean spherical errors are PHAT **25.6583 deg**, coherence **27.3902 deg**, harmonic **26.4940 deg**, combined **29.8588 deg**. These are measured program outputs, not expected/theoretical or fabricated values. The tables below disclose all SNR/scene cells, tails, conditional failures and independent-sequence results. A combination must not be described as superior when its paired intervals/point estimates do not support that statement. Harmonic confounders, coherent distractors and planar-array elevation conditioning are structural limitations of this simple method, not test exclusions.

Host: **12th Gen Intel(R) Core(TM) i7-12700KF**, Windows-11-10.0.26300-SP0. Python 3.12.14, one thread requested through OpenBLAS/OMP/MKL/NumExpr environment variables and SciPy FFT workers=1. Timings use `perf_counter_ns` over a shared front end (including the detector and estimated base) plus one method's search. Geometry construction (0.005813 s), warm-up, signal generation, disk I/O, plotting and the 200 ms acquisition window are excluded. Per-method timings share the same front end; their sum double counts it. Compute throughput is not acquisition/output cadence, nor end-to-end device performance. Window plus p95 is the nominal 200 ms frame fill plus measured p95 compute, excluding hardware/buffering/transport/display. Workstation background load and process scheduling were not isolated. The benchmark does not certify the organizer's target hardware.

## Artifacts and reproduction

- `code/experiment.py --self-test`: runnable assertions for wrap/zenith/antipodal metrics, calibration rank, known-direction localization, deterministic synthesis, exact SNR, steering sign, causal wrap and bounded hold. Actual self-test record: `results/self_test.json`.
- `code/experiment.py --quick` and `--full`: full pipeline with separate outputs. Completed runs are protected from silent overwrite. Move their output folders intentionally to rerun.
- `code/summarize_experiment.py results/full`: rebuild reports/tables/figures from saved CSV without rerunning acoustics.
- `code/requirements-lock.txt`: exact installed Python 3.12 package versions. Dependencies used locally are in `.python-packages`; the script inserts that directory only under Python 3.12 to avoid loading incompatible NumPy wheels into 3.10.
- All static validation/test/sensitivity audio, not just examples, is float32 in `data/synthetic/quick/validation`, `test`, `sensitivity`; filenames are trial IDs, sample-major shape (1600,8), unscaled mixtures. Seed tuples, actual geometry/delays, sample rate, frame truth and nominal array are embedded. Continuous tracking recordings are saved under `sequences`; a representative sequence and each static nuisance/label example additionally have 8-channel PCM16 WAV copies and scale sidecars.
- `test_frames.csv`, `sensitivity_frames.csv`, `tracking_frames.csv` contain raw per-frame/per-method outputs; repeated static method rows are paired observations, not independent trials. `validation_negatives.csv` contains every calibration score. `manifest.jsonl`, `config.json`, `runtime_environment.json`, `summary.json`, `source_manifest.json` and SHA256 `artifact_manifest.json` support inspection and reconstruction. The latter hashes all experiment scripts, lock/readme, full result files, all synthetic recordings and generated figures (excluding its own self-reference). `verify_experiment.py` verifies the executed source hash, every listed artifact, exact counts, preserved gate/miss semantics and eight prespecified bit-exact waveform/estimator reconstructions. The saved `quick` folder is a prior engineering checkpoint with its own earlier source hash, not the final scientific run; its conditional intervals are not publication evidence.
- Figure pairs (7-inch source width, 300 dpi PNG, vector PDF): `array_and_spectrum`, `detection`, `detection_roc`, `localization`, `paired_improvements`, `tracking`, `sensitivity`, `acoustic_maps` under `figures/quick`. The example sequence is fixed by ID before evaluating results, not chosen for successful tracking. Acoustic maps use preselected test trial `pos-2-2-0` (directional broadband nuisance, -5 dB, replicate 0); all 3601 grid responses, including the single zenith, are in `acoustic_maps_fixed_trial.npz`, with peak azimuth/elevation in `acoustic_map_peaks.csv`. The map image shows the rectangular 0–87-degree elevation grid; a possible zenith peak is marked at 90 degrees. White x marks the target, orange circle the estimate and orange triangle the nuisance direction.

## Prior-method attribution for the manuscript author

The supplied Chen, Chen and Wang (2022) review, DOI 10.12141/j.issn.1000-565X.220277, establishes the broader TDOA/GCC, harmonic UAV acoustics and array background. The present equations are a particular reproducible implementation, not a reproduction of every published variant. Conventional SRP sums generalized pair correlations at geometric delays; see the primary article [Source Localization with Acoustic Sensor Arrays Using Generative Model Based Fitting with Sparse Constraints](https://pmc.ncbi.nlm.nih.gov/articles/PMC3545592/). The Welch coherence definition is documented by [SciPy 1.15.3](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.signal.coherence.html), citing Welch (1967). The manuscript should use its independently verified primary references for SRP-PHAT and drone harmonic localization; a new implementation is not evidence of methodological priority.

## Detection (rates, not percentages)

| group | positive_n | negative_n | tp | fp | tpr | fpr | balanced_accuracy | balanced_accuracy_ci95 |
|---|---|---|---|---|---|---|---|---|
| all | 60 | 40 | 3 | 4 | 0.0500 | 0.1000 | 0.4750 | [0.43333333333333335, 0.5166666666666667] |
| snr=-15 | 12 | 40 | 0 | 4 | 0.0000 | 0.1000 | 0.4500 | [0.4125, 0.4875] |
| snr=-10 | 12 | 40 | 0 | 4 | 0.0000 | 0.1000 | 0.4500 | [0.4125, 0.4875] |
| snr=-5 | 12 | 40 | 0 | 4 | 0.0000 | 0.1000 | 0.4500 | [0.4125, 0.4875] |
| snr=0 | 12 | 40 | 0 | 4 | 0.0000 | 0.1000 | 0.4500 | [0.4125, 0.4875] |
| snr=5 | 12 | 40 | 3 | 4 | 0.2500 | 0.1000 | 0.5750 | [0.4708333333333333, 0.6708333333333333] |
| sensor_noise | 15 | 10 | 0 | 0 | 0.0000 | 0.0000 | 0.5000 | [0.5, 0.5] |
| wind | 15 | 10 | 1 | 0 | 0.0667 | 0.0000 | 0.5333 | [0.5, 0.6] |
| directional | 15 | 10 | 0 | 0 | 0.0000 | 0.0000 | 0.5000 | [0.5, 0.5] |
| engine | 15 | 10 | 2 | 4 | 0.1333 | 0.4000 | 0.3667 | [0.21625000000000003, 0.5166666666666666] |

## Unconditional and detected-only localization

| method | group | n | mean_deg | median_deg | p95_deg | azimuth_mae_deg | elevation_mae_deg | detected_n | detected_mean_deg | joint_detection_within10_rate |
|---|---|---|---|---|---|---|---|---|---|---|
| phat | all | 60 | 25.6583 | 2.5732 | 111.0706 | 30.8177 | 8.6546 | 3 | 1.3823 | 0.0500 |
| phat | snr=-15 | 12 | 30.3518 | 10.1558 | 92.5753 | 31.6333 | 15.1977 | 0 | NA | 0.0000 |
| phat | snr=-10 | 12 | 44.2091 | 10.7652 | 125.1315 | 52.9385 | 11.0195 | 0 | NA | 0.0000 |
| phat | snr=-5 | 12 | 32.8298 | 1.8266 | 117.4648 | 33.6432 | 10.6658 | 0 | NA | 0.0000 |
| phat | snr=0 | 12 | 19.0215 | 2.2478 | 72.2829 | 34.9542 | 4.7779 | 0 | NA | 0.0000 |
| phat | snr=5 | 12 | 1.8793 | 1.8542 | 3.2101 | 0.9193 | 1.6121 | 3 | 1.3823 | 0.2500 |
| phat | sensor_noise | 15 | 3.3331 | 1.8106 | 9.8271 | 1.3467 | 3.1143 | 0 | NA | 0.0000 |
| phat | wind | 15 | 1.6028 | 1.4182 | 3.1729 | 1.0336 | 1.3144 | 1 | 3.1558 | 0.0667 |
| phat | directional | 15 | 59.4295 | 67.8058 | 115.9796 | 77.7648 | 18.8438 | 0 | NA | 0.0000 |
| phat | engine | 15 | 38.2678 | 4.3926 | 123.3764 | 43.1257 | 11.3459 | 2 | 0.4955 | 0.1333 |
| phat | sensor_noise:-15 | 3 | 9.5979 | 9.3341 | 10.8131 | 2.6166 | 9.2171 | 0 | NA | 0.0000 |
| phat | sensor_noise:-10 | 3 | 1.8335 | 1.2467 | 3.1207 | 0.7794 | 1.6607 | 0 | NA | 0.0000 |
| phat | sensor_noise:-5 | 3 | 0.9924 | 0.9658 | 1.0607 | 1.8268 | 0.7988 | 0 | NA | 0.0000 |
| phat | sensor_noise:0 | 3 | 2.5070 | 2.7968 | 3.5777 | 0.9041 | 2.2276 | 0 | NA | 0.0000 |
| phat | sensor_noise:5 | 3 | 1.7346 | 1.8106 | 1.8891 | 0.6068 | 1.6673 | 0 | NA | 0.0000 |
| phat | wind:-15 | 3 | 0.9641 | 0.8557 | 1.3431 | 0.7030 | 0.7388 | 0 | NA | 0.0000 |
| phat | wind:-10 | 3 | 1.2353 | 1.4182 | 1.7299 | 1.6842 | 0.7702 | 0 | NA | 0.0000 |
| phat | wind:-5 | 3 | 1.9173 | 2.0440 | 2.5673 | 0.8719 | 1.7232 | 0 | NA | 0.0000 |
| phat | wind:0 | 3 | 0.9343 | 0.6904 | 1.3643 | 1.1058 | 0.5015 | 0 | NA | 0.0000 |
| phat | wind:5 | 3 | 2.9632 | 3.1558 | 3.2072 | 0.8028 | 2.8382 | 1 | 3.1558 | 0.3333 |
| phat | directional:-15 | 3 | 45.8915 | 46.2039 | 74.6598 | 52.2367 | 21.0367 | 0 | NA | 0.0000 |
| phat | directional:-10 | 3 | 83.8895 | 74.6982 | 102.0421 | 99.5722 | 23.2577 | 0 | NA | 0.0000 |
| phat | directional:-5 | 3 | 95.2218 | 87.4906 | 136.0192 | 98.7242 | 34.4175 | 0 | NA | 0.0000 |
| phat | directional:0 | 3 | 70.2013 | 67.8058 | 76.7599 | 136.4608 | 14.2411 | 0 | NA | 0.0000 |
| phat | directional:5 | 3 | 1.9433 | 2.0003 | 3.0870 | 1.8299 | 1.2659 | 0 | NA | 0.0000 |
| phat | engine:-15 | 3 | 64.9537 | 75.6859 | 107.1155 | 70.9770 | 29.7983 | 0 | NA | 0.0000 |
| phat | engine:-10 | 3 | 89.8782 | 119.8661 | 130.3970 | 109.7182 | 18.3894 | 0 | NA | 0.0000 |
| phat | engine:-5 | 3 | 33.1876 | 1.6091 | 88.2458 | 33.1498 | 5.7238 | 0 | NA | 0.0000 |
| phat | engine:0 | 3 | 2.4432 | 1.6988 | 4.1233 | 1.3459 | 2.1413 | 0 | NA | 0.0000 |
| phat | engine:5 | 3 | 0.8761 | 0.6859 | 1.5421 | 0.4376 | 0.6768 | 2 | 0.4955 | 0.6667 |
| coherence | all | 60 | 27.3902 | 2.7111 | 111.0706 | 32.8359 | 9.0638 | 3 | 1.3823 | 0.0500 |
| coherence | snr=-15 | 12 | 31.6390 | 12.6764 | 92.5753 | 31.7245 | 16.4477 | 0 | NA | 0.0000 |
| coherence | snr=-10 | 12 | 44.5993 | 10.7652 | 125.1315 | 53.1885 | 11.3229 | 0 | NA | 0.0000 |
| coherence | snr=-5 | 12 | 39.5620 | 2.3347 | 117.4648 | 43.3932 | 10.9083 | 0 | NA | 0.0000 |
| coherence | snr=0 | 12 | 19.2715 | 2.2478 | 73.6329 | 34.9542 | 5.0279 | 0 | NA | 0.0000 |
| coherence | snr=5 | 12 | 1.8793 | 1.8542 | 3.2101 | 0.9193 | 1.6121 | 3 | 1.3823 | 0.2500 |
| coherence | sensor_noise | 15 | 4.3641 | 1.8651 | 14.5339 | 1.3467 | 4.1570 | 0 | NA | 0.0000 |
| coherence | wind | 15 | 1.6428 | 1.4182 | 3.1729 | 1.1065 | 1.3144 | 1 | 3.1558 | 0.0667 |
| coherence | directional | 15 | 59.9005 | 67.8058 | 115.9796 | 77.9648 | 19.2438 | 0 | NA | 0.0000 |
| coherence | engine | 15 | 43.6536 | 8.5676 | 123.3764 | 50.9257 | 11.5399 | 2 | 0.4955 | 0.1333 |
| coherence | sensor_noise:-15 | 3 | 14.5471 | 11.7038 | 20.1942 | 2.6166 | 14.2171 | 0 | NA | 0.0000 |
| coherence | sensor_noise:-10 | 3 | 2.0396 | 1.8651 | 3.1826 | 0.7794 | 1.8742 | 0 | NA | 0.0000 |
| coherence | sensor_noise:-5 | 3 | 0.9924 | 0.9658 | 1.0607 | 1.8268 | 0.7988 | 0 | NA | 0.0000 |
| coherence | sensor_noise:0 | 3 | 2.5070 | 2.7968 | 3.5777 | 0.9041 | 2.2276 | 0 | NA | 0.0000 |
| coherence | sensor_noise:5 | 3 | 1.7346 | 1.8106 | 1.8891 | 0.6068 | 1.6673 | 0 | NA | 0.0000 |
| coherence | wind:-15 | 3 | 1.1638 | 1.2383 | 1.3814 | 1.0675 | 0.7388 | 0 | NA | 0.0000 |
| coherence | wind:-10 | 3 | 1.2353 | 1.4182 | 1.7299 | 1.6842 | 0.7702 | 0 | NA | 0.0000 |
| coherence | wind:-5 | 3 | 1.9173 | 2.0440 | 2.5673 | 0.8719 | 1.7232 | 0 | NA | 0.0000 |
| coherence | wind:0 | 3 | 0.9343 | 0.6904 | 1.3643 | 1.1058 | 0.5015 | 0 | NA | 0.0000 |
| coherence | wind:5 | 3 | 2.9632 | 3.1558 | 3.2072 | 0.8028 | 2.8382 | 1 | 3.1558 | 0.3333 |
| coherence | directional:-15 | 3 | 45.8915 | 46.2039 | 74.6598 | 52.2367 | 21.0367 | 0 | NA | 0.0000 |
| coherence | directional:-10 | 3 | 85.2442 | 75.9542 | 102.1677 | 100.5722 | 24.2577 | 0 | NA | 0.0000 |
| coherence | directional:-5 | 3 | 95.2218 | 87.4906 | 136.0192 | 98.7242 | 34.4175 | 0 | NA | 0.0000 |
| coherence | directional:0 | 3 | 71.2013 | 67.8058 | 79.4599 | 136.4608 | 15.2411 | 0 | NA | 0.0000 |
| coherence | directional:5 | 3 | 1.9433 | 2.0003 | 3.0870 | 1.8299 | 1.2659 | 0 | NA | 0.0000 |
| coherence | engine:-15 | 3 | 64.9537 | 75.6859 | 107.1155 | 70.9770 | 29.7983 | 0 | NA | 0.0000 |
| coherence | engine:-10 | 3 | 89.8782 | 119.8661 | 130.3970 | 109.7182 | 18.3894 | 0 | NA | 0.0000 |
| coherence | engine:-5 | 3 | 60.1165 | 80.8684 | 96.1717 | 72.1498 | 6.6935 | 0 | NA | 0.0000 |
| coherence | engine:0 | 3 | 2.4432 | 1.6988 | 4.1233 | 1.3459 | 2.1413 | 0 | NA | 0.0000 |
| coherence | engine:5 | 3 | 0.8761 | 0.6859 | 1.5421 | 0.4376 | 0.6768 | 2 | 0.4955 | 0.6667 |
| harmonic | all | 60 | 26.4940 | 2.6250 | 111.0706 | 29.7683 | 9.3507 | 3 | 1.3823 | 0.0500 |
| harmonic | snr=-15 | 12 | 34.8626 | 12.3132 | 92.5753 | 38.4371 | 17.9769 | 0 | NA | 0.0000 |
| harmonic | snr=-10 | 12 | 44.6856 | 12.6960 | 125.1315 | 53.1670 | 11.4872 | 0 | NA | 0.0000 |
| harmonic | snr=-5 | 12 | 44.1565 | 29.6945 | 117.4648 | 48.9119 | 12.3650 | 0 | NA | 0.0000 |
| harmonic | snr=0 | 12 | 6.8858 | 1.3387 | 31.6855 | 7.4062 | 3.3122 | 0 | NA | 0.0000 |
| harmonic | snr=5 | 12 | 1.8793 | 1.8542 | 3.2101 | 0.9193 | 1.6121 | 3 | 1.3823 | 0.2500 |
| harmonic | sensor_noise | 15 | 7.2666 | 1.8106 | 28.2197 | 6.5893 | 5.7451 | 0 | NA | 0.0000 |
| harmonic | wind | 15 | 1.5890 | 1.4391 | 3.1729 | 1.2164 | 1.2861 | 1 | 3.1558 | 0.0667 |
| harmonic | directional | 15 | 49.9172 | 56.7636 | 115.9796 | 55.7770 | 17.8438 | 0 | NA | 0.0000 |
| harmonic | engine | 15 | 47.2032 | 18.2014 | 123.3764 | 55.4905 | 12.5277 | 2 | 0.4955 | 0.1333 |
| harmonic | sensor_noise:-15 | 3 | 28.4389 | 10.9774 | 62.7041 | 29.8316 | 21.2338 | 0 | NA | 0.0000 |
| harmonic | sensor_noise:-10 | 3 | 3.8148 | 3.3289 | 6.8044 | 0.7794 | 3.6607 | 0 | NA | 0.0000 |
| harmonic | sensor_noise:-5 | 3 | 0.8187 | 0.9401 | 0.9632 | 1.0775 | 0.7988 | 0 | NA | 0.0000 |
| harmonic | sensor_noise:0 | 3 | 1.5258 | 0.6733 | 3.3653 | 0.6512 | 1.3648 | 0 | NA | 0.0000 |
| harmonic | sensor_noise:5 | 3 | 1.7346 | 1.8106 | 1.8891 | 0.6068 | 1.6673 | 0 | NA | 0.0000 |
| harmonic | wind:-15 | 3 | 1.0617 | 0.8557 | 1.6066 | 0.7030 | 0.8387 | 0 | NA | 0.0000 |
| harmonic | wind:-10 | 3 | 1.1600 | 1.2103 | 1.6930 | 2.5983 | 0.6411 | 0 | NA | 0.0000 |
| harmonic | wind:-5 | 3 | 1.8256 | 1.7688 | 2.5398 | 0.8719 | 1.6110 | 0 | NA | 0.0000 |
| harmonic | wind:0 | 3 | 0.9343 | 0.6904 | 1.3643 | 1.1058 | 0.5015 | 0 | NA | 0.0000 |
| harmonic | wind:5 | 3 | 2.9632 | 3.1558 | 3.2072 | 0.8028 | 2.8382 | 1 | 3.1558 | 0.3333 |
| harmonic | directional:-15 | 3 | 45.8915 | 46.2039 | 74.6598 | 52.2367 | 21.0367 | 0 | NA | 0.0000 |
| harmonic | directional:-10 | 3 | 83.8895 | 74.6982 | 102.0421 | 99.5722 | 23.2577 | 0 | NA | 0.0000 |
| harmonic | directional:-5 | 3 | 95.2218 | 87.4906 | 136.0192 | 98.7242 | 34.4175 | 0 | NA | 0.0000 |
| harmonic | directional:0 | 3 | 22.6397 | 2.6246 | 58.8015 | 26.5218 | 9.2411 | 0 | NA | 0.0000 |
| harmonic | directional:5 | 3 | 1.9433 | 2.0003 | 3.0870 | 1.8299 | 1.2659 | 0 | NA | 0.0000 |
| harmonic | engine:-15 | 3 | 64.0583 | 72.9996 | 106.8468 | 70.9770 | 28.7983 | 0 | NA | 0.0000 |
| harmonic | engine:-10 | 3 | 89.8782 | 119.8661 | 130.3970 | 109.7182 | 18.3894 | 0 | NA | 0.0000 |
| harmonic | engine:-5 | 3 | 78.7600 | 80.8684 | 96.1717 | 94.9740 | 12.6327 | 0 | NA | 0.0000 |
| harmonic | engine:0 | 3 | 2.4432 | 1.6988 | 4.1233 | 1.3459 | 2.1413 | 0 | NA | 0.0000 |
| harmonic | engine:5 | 3 | 0.8761 | 0.6859 | 1.5421 | 0.4376 | 0.6768 | 2 | 0.4955 | 0.6667 |
| combined | all | 60 | 29.8588 | 2.8906 | 120.4511 | 33.8365 | 8.8111 | 3 | 1.3823 | 0.0500 |
| combined | snr=-15 | 12 | 38.7483 | 11.1083 | 114.1457 | 45.0282 | 15.2269 | 0 | NA | 0.0000 |
| combined | snr=-10 | 12 | 44.7773 | 10.7652 | 125.1315 | 53.4170 | 11.5195 | 0 | NA | 0.0000 |
| combined | snr=-5 | 12 | 44.1664 | 29.6945 | 117.4648 | 49.1619 | 12.3650 | 0 | NA | 0.0000 |
| combined | snr=0 | 12 | 19.7048 | 1.5690 | 105.5082 | 20.6562 | 3.3122 | 0 | NA | 0.0000 |
| combined | snr=5 | 12 | 1.8974 | 1.8542 | 3.2101 | 0.9193 | 1.6317 | 3 | 1.3823 | 0.2500 |
| combined | sensor_noise | 15 | 9.9612 | 1.7120 | 41.0092 | 11.9893 | 3.1608 | 0 | NA | 0.0000 |
| combined | wind | 15 | 1.8276 | 1.6901 | 3.2330 | 1.2893 | 1.5119 | 1 | 3.1558 | 0.0667 |
| combined | directional | 15 | 50.1881 | 56.7636 | 115.9796 | 55.9770 | 18.0438 | 0 | NA | 0.0000 |
| combined | engine | 15 | 57.4584 | 57.5396 | 138.5865 | 66.0905 | 12.5277 | 2 | 0.4955 | 0.1333 |
| combined | sensor_noise:-15 | 3 | 43.7819 | 7.8117 | 107.4041 | 55.8316 | 10.2338 | 0 | NA | 0.0000 |
| combined | sensor_noise:-10 | 3 | 1.8335 | 1.2467 | 3.1207 | 0.7794 | 1.6607 | 0 | NA | 0.0000 |
| combined | sensor_noise:-5 | 3 | 0.8581 | 0.9658 | 1.0489 | 2.0775 | 0.7988 | 0 | NA | 0.0000 |
| combined | sensor_noise:0 | 3 | 1.5258 | 0.6733 | 3.3653 | 0.6512 | 1.3648 | 0 | NA | 0.0000 |
| combined | sensor_noise:5 | 3 | 1.8068 | 1.8106 | 1.8891 | 0.6068 | 1.7460 | 0 | NA | 0.0000 |
| combined | wind:-15 | 3 | 1.2614 | 1.2383 | 1.6449 | 1.0675 | 0.8387 | 0 | NA | 0.0000 |
| combined | wind:-10 | 3 | 2.1534 | 1.9698 | 3.1490 | 2.5983 | 1.7702 | 0 | NA | 0.0000 |
| combined | wind:-5 | 3 | 1.8256 | 1.7688 | 2.5398 | 0.8719 | 1.6110 | 0 | NA | 0.0000 |
| combined | wind:0 | 3 | 0.9343 | 0.6904 | 1.3643 | 1.1058 | 0.5015 | 0 | NA | 0.0000 |
| combined | wind:5 | 3 | 2.9632 | 3.1558 | 3.2072 | 0.8028 | 2.8382 | 1 | 3.1558 | 0.3333 |
| combined | directional:-15 | 3 | 45.8915 | 46.2039 | 74.6598 | 52.2367 | 21.0367 | 0 | NA | 0.0000 |
| combined | directional:-10 | 3 | 85.2442 | 75.9542 | 102.1677 | 100.5722 | 24.2577 | 0 | NA | 0.0000 |
| combined | directional:-5 | 3 | 95.2218 | 87.4906 | 136.0192 | 98.7242 | 34.4175 | 0 | NA | 0.0000 |
| combined | directional:0 | 3 | 22.6397 | 2.6246 | 58.8015 | 26.5218 | 9.2411 | 0 | NA | 0.0000 |
| combined | directional:5 | 3 | 1.9433 | 2.0003 | 3.0870 | 1.8299 | 1.2659 | 0 | NA | 0.0000 |
| combined | engine:-15 | 3 | 64.0583 | 72.9996 | 106.8468 | 70.9770 | 28.7983 | 0 | NA | 0.0000 |
| combined | engine:-10 | 3 | 89.8782 | 119.8661 | 130.3970 | 109.7182 | 18.3894 | 0 | NA | 0.0000 |
| combined | engine:-5 | 3 | 78.7600 | 80.8684 | 96.1717 | 94.9740 | 12.6327 | 0 | NA | 0.0000 |
| combined | engine:0 | 3 | 53.7195 | 4.4946 | 139.9181 | 54.3459 | 2.1413 | 0 | NA | 0.0000 |
| combined | engine:5 | 3 | 0.8761 | 0.6859 | 1.5421 | 0.4376 | 0.6768 | 2 | 0.4955 | 0.6667 |

## Paired localization improvements (positive is better than PHAT)

| method | group | n | baseline_minus_method_mean_deg | ci95_low | ci95_high |
|---|---|---|---|---|---|
| coherence | all | 60 | -1.7319 | -4.3183 | -0.1628 |
| coherence | snr=-15 | 12 | -1.2872 | -3.0008 | -0.2315 |
| coherence | snr=-10 | 12 | -0.3902 | -1.0173 | 0.0000 |
| coherence | snr=-5 | 12 | -6.7322 | -20.1967 | 0.0000 |
| coherence | snr=0 | 12 | -0.2500 | -0.7500 | 0.0000 |
| coherence | snr=5 | 12 | 0.0000 | 0.0000 | 0.0000 |
| coherence | sensor_noise | 15 | -1.0311 | -2.4019 | -0.1865 |
| coherence | wind | 15 | -0.0399 | -0.1198 | 0.0000 |
| coherence | directional | 15 | -0.4709 | -1.0128 | 0.0000 |
| coherence | engine | 15 | -5.3858 | -16.1574 | 0.0000 |
| harmonic | all | 60 | -0.8357 | -4.0057 | 2.3699 |
| harmonic | snr=-15 | 12 | -4.5108 | -14.5799 | 0.8634 |
| harmonic | snr=-10 | 12 | -0.4765 | -1.4672 | 0.0361 |
| harmonic | snr=-5 | 12 | -11.3268 | -20.1304 | 0.0459 |
| harmonic | snr=0 | 12 | 12.1357 | 0.2453 | 19.4755 |
| harmonic | snr=5 | 12 | 0.0000 | 0.0000 | 0.0000 |
| harmonic | sensor_noise | 15 | -3.9335 | -11.8530 | 0.6027 |
| harmonic | wind | 15 | 0.0139 | -0.0367 | 0.0644 |
| harmonic | directional | 15 | 9.5123 | 0.0000 | 15.5008 |
| harmonic | engine | 15 | -8.9354 | -15.9783 | 0.1791 |
| combined | all | 60 | -4.2005 | -10.2392 | 1.3015 |
| combined | snr=-15 | 12 | -8.3965 | -27.1344 | 1.6135 |
| combined | snr=-10 | 12 | -0.5682 | -1.2456 | 0.0175 |
| combined | snr=-5 | 12 | -11.3366 | -20.1402 | 0.0360 |
| combined | snr=0 | 12 | -0.6833 | -25.1215 | 18.1429 |
| combined | snr=5 | 12 | -0.0181 | -0.0542 | 0.0000 |
| combined | sensor_noise | 15 | -6.6281 | -21.5849 | 1.3487 |
| combined | wind | 15 | -0.2247 | -0.5733 | 0.0129 |
| combined | directional | 15 | 9.2414 | 0.0000 | 14.9589 |
| combined | engine | 15 | -19.1907 | -38.6917 | -3.9432 |

## Sensor-error sensitivity (positive increase is worse)

| method | condition | n | mean_deg | increase_vs_nominal_deg | ci95_low | ci95_high |
|---|---|---|---|---|---|---|
| phat | nominal | 12 | 16.8975 | 0.0000 | 0.0000 | 0.0000 |
| phat | position_5mm | 12 | 17.9204 | 1.0228 | 1.0228 | 1.0228 |
| phat | delay_20us | 12 | 18.5400 | 1.6425 | 1.6425 | 1.6425 |
| phat | both | 12 | 18.2616 | 1.3640 | 1.3640 | 1.3640 |
| coherence | nominal | 12 | 16.8973 | 0.0000 | 0.0000 | 0.0000 |
| coherence | position_5mm | 12 | 17.9071 | 1.0098 | 1.0098 | 1.0098 |
| coherence | delay_20us | 12 | 18.5400 | 1.6427 | 1.6427 | 1.6427 |
| coherence | both | 12 | 18.1166 | 1.2193 | 1.2193 | 1.2193 |
| harmonic | nominal | 12 | 19.5752 | 0.0000 | 0.0000 | 0.0000 |
| harmonic | position_5mm | 12 | 20.1500 | 0.5748 | 0.5748 | 0.5748 |
| harmonic | delay_20us | 12 | 20.9745 | 1.3993 | 1.3993 | 1.3993 |
| harmonic | both | 12 | 20.3547 | 0.7795 | 0.7795 | 0.7795 |
| combined | nominal | 12 | 19.5752 | 0.0000 | 0.0000 | 0.0000 |
| combined | position_5mm | 12 | 20.1500 | 0.5748 | 0.5748 | 0.5748 |
| combined | delay_20us | 12 | 20.9461 | 1.3709 | 1.3709 | 1.3709 |
| combined | both | 12 | 20.1638 | 0.5886 | 0.5886 | 0.5886 |

## Tracking (equal-weight means of independent sequence metrics)

| method | mode | sequences | sequences_with_output | coverage | mean_deg | p95_deg | turn_mean_deg | within10_all_positive_rate | chord_velocity_rmse_deg_s | absent_output_rate |
|---|---|---|---|---|---|---|---|---|---|---|
| phat | raw | 12 | 12 | 1.0000 | 15.2123 | 26.1401 | 14.5579 | 0.7208 | 28.0991 | 1.0000 |
| phat | smooth_all | 12 | 12 | 1.0000 | 19.2961 | 36.4327 | 16.0924 | 0.5875 | 23.1514 | 1.0000 |
| phat | gated | 12 | 1 | 0.0125 | 54.2162 | 56.1912 | NA | 0.0000 | 23.5656 | 0.1167 |
| coherence | raw | 12 | 12 | 1.0000 | 15.8899 | 30.8552 | 14.5148 | 0.7042 | 32.4282 | 1.0000 |
| coherence | smooth_all | 12 | 12 | 1.0000 | 19.4505 | 36.4280 | 15.9622 | 0.5708 | 23.0408 | 1.0000 |
| coherence | gated | 12 | 1 | 0.0125 | 54.2162 | 56.1912 | NA | 0.0000 | 23.5656 | 0.1167 |
| harmonic | raw | 12 | 12 | 1.0000 | 18.4470 | 31.9631 | 17.8328 | 0.6583 | 29.0309 | 1.0000 |
| harmonic | smooth_all | 12 | 12 | 1.0000 | 22.2131 | 42.3163 | 18.1433 | 0.5333 | 24.1318 | 1.0000 |
| harmonic | gated | 12 | 1 | 0.0125 | 55.6870 | 57.6290 | NA | 0.0000 | 19.0968 | 0.1167 |
| combined | raw | 12 | 12 | 1.0000 | 19.2079 | 32.0397 | 18.9544 | 0.6375 | 29.0841 | 1.0000 |
| combined | smooth_all | 12 | 12 | 1.0000 | 22.8306 | 41.7397 | 19.3622 | 0.5083 | 23.3326 | 1.0000 |
| combined | gated | 12 | 1 | 0.0125 | 55.6870 | 57.6290 | NA | 0.0000 | 19.0968 | 0.1167 |

### Tracking detection continuity, latency and paired intervals

| method | mode | detection_recall | detection_fpr | max_miss_s | sequences_with_detection | first_detection_delay_s | five_second_window_pass_rate |
|---|---|---|---|---|---|---|---|
| phat | raw | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| phat | smooth_all | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| phat | gated | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| coherence | raw | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| coherence | smooth_all | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| coherence | gated | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| harmonic | raw | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| harmonic | smooth_all | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| harmonic | gated | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| combined | raw | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| combined | smooth_all | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |
| combined | gated | 0.0083 | 0.0375 | 3.9667 | 1 | 3.8000 | NA |

| method | independent_sequences | mean_deg | ci95 |
|---|---|---|---|
| phat | 12 | -4.0838 | [-6.132433693311491, -2.2081767760586573] |
| coherence | 12 | -3.5606 | [-5.2889832304328985, -1.9313917888089946] |
| harmonic | 12 | -3.7661 | [-6.327723897052362, -1.592691165385299] |
| combined | 12 | -3.6227 | [-5.931036537062542, -1.556316395231937] |

## Host-only processing benchmark

| method | n | median_ms | p95_ms | max_ms | compute_throughput_fps | window_plus_p95_ms |
|---|---|---|---|---|---|---|
| phat | 100 | 5.4601 | 7.3549 | 7.8917 | 180.0573 | 207.3549 |
| coherence | 100 | 5.7968 | 7.6929 | 9.2987 | 170.7830 | 207.6929 |
| harmonic | 100 | 5.7663 | 7.6820 | 10.3109 | 170.1159 | 207.6820 |
| combined | 100 | 5.6319 | 7.7261 | 8.5587 | 171.8627 | 207.7261 |

## Per-sequence results (no sequence discarded)

| sequence_id | scene | snr_db | method | mode | coverage | mean_deg | p95_deg | turn_mean_deg | within10_all_positive_rate | max_miss_s |
|---|---|---|---|---|---|---|---|---|---|---|
| seq-0-0-0 | sensor_noise | -10.0000 | phat | raw | 1.0000 | 3.7108 | 6.7266 | 3.5451 | 1.0000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | phat | smooth_all | 1.0000 | 9.6065 | 28.3037 | 5.9491 | 0.8000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | coherence | raw | 1.0000 | 3.4323 | 6.7415 | 2.9341 | 0.9500 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | coherence | smooth_all | 1.0000 | 9.3613 | 28.2551 | 5.4670 | 0.8000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | harmonic | raw | 1.0000 | 4.0350 | 6.2136 | 4.3512 | 1.0000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | harmonic | smooth_all | 1.0000 | 10.2111 | 32.6099 | 6.1742 | 0.8000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | combined | raw | 1.0000 | 3.6874 | 6.5023 | 3.3485 | 1.0000 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | combined | smooth_all | 1.0000 | 10.1559 | 34.8111 | 5.2124 | 0.7500 | 4.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | phat | raw | 1.0000 | 1.8986 | 4.4210 | 1.8168 | 1.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | phat | smooth_all | 1.0000 | 6.8514 | 15.4815 | 4.1207 | 0.9000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | coherence | raw | 1.0000 | 1.8479 | 4.1854 | 1.8103 | 1.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | coherence | smooth_all | 1.0000 | 7.9906 | 23.7630 | 3.5177 | 0.8500 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | harmonic | raw | 1.0000 | 1.9522 | 3.9184 | 1.9051 | 1.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | harmonic | smooth_all | 1.0000 | 5.1462 | 8.8292 | 4.3811 | 1.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | combined | raw | 1.0000 | 2.0755 | 5.3358 | 1.8518 | 1.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | combined | smooth_all | 1.0000 | 5.9430 | 8.9931 | 4.6407 | 1.0000 | 4.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | phat | raw | 1.0000 | 1.5670 | 2.6821 | 1.3504 | 1.0000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | phat | smooth_all | 1.0000 | 8.3429 | 24.2335 | 4.9888 | 0.8500 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | coherence | raw | 1.0000 | 1.5852 | 2.6821 | 1.3549 | 1.0000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | coherence | smooth_all | 1.0000 | 8.3933 | 25.1045 | 4.8231 | 0.8000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | harmonic | raw | 1.0000 | 1.5584 | 3.0753 | 1.1338 | 1.0000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | harmonic | smooth_all | 1.0000 | 13.0184 | 48.4675 | 5.2189 | 0.7500 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | combined | raw | 1.0000 | 1.4746 | 2.4025 | 1.1338 | 1.0000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | combined | smooth_all | 1.0000 | 10.7390 | 37.9471 | 4.8338 | 0.8000 | 4.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | phat | raw | 1.0000 | 1.1493 | 1.5730 | 1.1154 | 1.0000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | phat | smooth_all | 1.0000 | 12.7717 | 43.9004 | 5.8826 | 0.7500 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | coherence | raw | 1.0000 | 1.1865 | 1.9696 | 1.1482 | 1.0000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | coherence | smooth_all | 1.0000 | 6.7849 | 13.1677 | 5.2145 | 0.9000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | harmonic | raw | 1.0000 | 1.2177 | 2.2469 | 1.1154 | 1.0000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | harmonic | smooth_all | 1.0000 | 12.3819 | 39.8339 | 6.1443 | 0.7500 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | combined | raw | 1.0000 | 1.1789 | 2.1352 | 1.1154 | 1.0000 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | combined | smooth_all | 1.0000 | 11.7951 | 36.9820 | 6.0642 | 0.7500 | 4.0000 |
| seq-1-0-0 | wind | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | phat | raw | 1.0000 | 1.3374 | 2.1169 | 1.1032 | 1.0000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | phat | smooth_all | 1.0000 | 8.7147 | 25.1917 | 6.4359 | 0.8500 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | coherence | raw | 1.0000 | 1.3929 | 2.4534 | 1.1032 | 1.0000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | coherence | smooth_all | 1.0000 | 9.6833 | 32.3102 | 6.0849 | 0.8000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | harmonic | raw | 1.0000 | 1.3812 | 2.4534 | 1.1032 | 1.0000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | harmonic | smooth_all | 1.0000 | 8.3062 | 21.1806 | 6.8828 | 0.8500 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | combined | raw | 1.0000 | 1.3929 | 2.4534 | 1.1032 | 1.0000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | combined | smooth_all | 1.0000 | 9.3816 | 26.4867 | 6.9718 | 0.8000 | 4.0000 |
| seq-1-1-0 | wind | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | phat | raw | 1.0000 | 1.0878 | 1.9410 | 0.9140 | 1.0000 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | phat | smooth_all | 1.0000 | 5.6848 | 7.9952 | 4.6424 | 0.9500 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | coherence | raw | 1.0000 | 1.0856 | 1.9387 | 0.9140 | 1.0000 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | coherence | smooth_all | 1.0000 | 6.5795 | 10.1497 | 5.1096 | 0.9500 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | harmonic | raw | 1.0000 | 1.0445 | 1.6797 | 0.9140 | 1.0000 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | harmonic | smooth_all | 1.0000 | 6.0428 | 10.2058 | 4.5306 | 0.9500 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | combined | raw | 1.0000 | 1.0422 | 1.6774 | 0.9140 | 1.0000 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | combined | smooth_all | 1.0000 | 5.4561 | 8.3912 | 4.5653 | 0.9500 | 4.0000 |
| seq-1-2-0 | wind | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | phat | raw | 1.0000 | 39.9477 | 58.5861 | 33.8200 | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | phat | smooth_all | 1.0000 | 39.9477 | 58.5861 | 33.8200 | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | coherence | raw | 1.0000 | 39.9477 | 58.5861 | 33.8200 | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | coherence | smooth_all | 1.0000 | 39.9477 | 58.5861 | 33.8200 | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | harmonic | raw | 1.0000 | 39.9477 | 58.5861 | 33.8200 | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | harmonic | smooth_all | 1.0000 | 39.9477 | 58.5861 | 33.8200 | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | combined | raw | 1.0000 | 39.9477 | 58.5861 | 33.8200 | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | combined | smooth_all | 1.0000 | 39.9517 | 58.5861 | 33.8210 | 0.0000 | 4.0000 |
| seq-2-0-0 | directional | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | phat | raw | 1.0000 | 67.8821 | 80.4210 | 71.5910 | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | phat | smooth_all | 1.0000 | 67.8821 | 80.4210 | 71.5910 | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | coherence | raw | 1.0000 | 67.8821 | 80.4210 | 71.5910 | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | coherence | smooth_all | 1.0000 | 67.8821 | 80.4210 | 71.5910 | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | harmonic | raw | 1.0000 | 67.7697 | 80.4210 | 71.5910 | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | harmonic | smooth_all | 1.0000 | 67.7751 | 80.4192 | 71.4569 | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | combined | raw | 1.0000 | 67.7697 | 80.4210 | 71.5910 | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | combined | smooth_all | 1.0000 | 67.7751 | 80.4192 | 71.4569 | 0.0000 | 4.0000 |
| seq-2-1-0 | directional | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | phat | raw | 1.0000 | 33.1661 | 56.7140 | 39.0355 | 0.4000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | phat | smooth_all | 1.0000 | 33.7350 | 53.1002 | 32.8239 | 0.1500 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | coherence | raw | 1.0000 | 33.1661 | 56.7140 | 39.0355 | 0.4000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | coherence | smooth_all | 1.0000 | 33.7350 | 53.1002 | 32.8239 | 0.1500 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | harmonic | raw | 1.0000 | 33.2996 | 56.7140 | 39.0355 | 0.4000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | harmonic | smooth_all | 1.0000 | 33.7810 | 53.4231 | 32.7927 | 0.2000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | combined | raw | 1.0000 | 33.2996 | 56.7140 | 39.0355 | 0.4000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | combined | smooth_all | 1.0000 | 33.7810 | 53.4231 | 32.7927 | 0.2000 | 4.0000 |
| seq-2-2-0 | directional | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | phat | raw | 1.0000 | 15.2410 | 39.9751 | 17.1704 | 0.5000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | phat | smooth_all | 1.0000 | 15.4943 | 29.9689 | 16.1760 | 0.4000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | coherence | raw | 1.0000 | 15.2410 | 39.9751 | 17.1704 | 0.5000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | coherence | smooth_all | 1.0000 | 15.4916 | 29.9669 | 16.1768 | 0.4000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | harmonic | raw | 1.0000 | 19.6780 | 45.6038 | 17.2497 | 0.4000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | harmonic | smooth_all | 1.0000 | 19.7182 | 45.6456 | 17.3024 | 0.4000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | combined | raw | 1.0000 | 19.6780 | 45.6038 | 17.2497 | 0.4000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | combined | smooth_all | 1.0000 | 19.7151 | 45.6267 | 17.3029 | 0.4000 | 4.0000 |
| seq-3-0-0 | engine | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-3-1-0 | engine | -5.0000 | phat | raw | 1.0000 | 11.4004 | 52.5793 | 2.1287 | 0.8000 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | phat | smooth_all | 1.0000 | 12.6729 | 39.6143 | 3.1704 | 0.6500 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | phat | gated | 0.1500 | 54.2162 | 56.1912 | NA | 0.0000 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | coherence | raw | 1.0000 | 13.7289 | 52.5793 | 2.1300 | 0.7500 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | coherence | smooth_all | 1.0000 | 14.6879 | 43.7741 | 3.3688 | 0.6000 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | coherence | gated | 0.1500 | 54.2162 | 56.1912 | NA | 0.0000 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | harmonic | raw | 1.0000 | 22.8893 | 54.7063 | 20.5399 | 0.5000 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | harmonic | smooth_all | 1.0000 | 23.1746 | 49.7313 | 15.0831 | 0.3000 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | harmonic | gated | 0.1500 | 55.6870 | 57.6290 | NA | 0.0000 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | combined | raw | 1.0000 | 32.4966 | 54.7063 | 35.0959 | 0.2500 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | combined | smooth_all | 1.0000 | 32.2999 | 51.1545 | 30.7740 | 0.0500 | 3.6000 |
| seq-3-1-0 | engine | -5.0000 | combined | gated | 0.1500 | 55.6870 | 57.6290 | NA | 0.0000 | 3.6000 |
| seq-3-2-0 | engine | 0.0000 | phat | raw | 1.0000 | 4.1599 | 5.9447 | 1.1038 | 0.9500 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | phat | smooth_all | 1.0000 | 9.8495 | 30.3959 | 3.5075 | 0.7500 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | coherence | raw | 1.0000 | 10.1827 | 62.0167 | 1.1662 | 0.8500 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | coherence | smooth_all | 1.0000 | 12.8692 | 38.5372 | 3.5492 | 0.6000 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | harmonic | raw | 1.0000 | 26.5910 | 67.9391 | 21.2353 | 0.6000 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | harmonic | smooth_all | 1.0000 | 27.0543 | 58.8629 | 13.9320 | 0.4000 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | combined | raw | 1.0000 | 26.4519 | 67.9391 | 21.1938 | 0.6000 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | combined | smooth_all | 1.0000 | 26.9737 | 58.0550 | 13.9107 | 0.4000 | 4.0000 |
| seq-3-2-0 | engine | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 4.0000 |
