# Exact method and results: simulation-only acoustic detection and direction estimation

This file is generated from executed CSV records. Run mode: **full**. Master seed: **20261002**. No organizer data, measured array, calibrated source levels, actual-flight localization labels, or target-device benchmark are used. The model's 20–80 m distance is solely a geometric curvature parameter: prescribed SNR is normalized independently of range. Neither 100 m detection nor a maximum effective range is established. No result from `data/public` is included here. This is an interpretable combination/ablation study, not a priority claim for SRP, PHAT, harmonic selection, coherence, or smoothing.

## Frozen experiment and independent units

800 validation negatives; 1000 test negatives; 1000 test positives. Positives are balanced across SNR = -15, -10, -5, 0, +5 dB and four nuisance scenes. Every static trial has fresh source, noise, direction, sound speed, source phases and gains. SNR cells do not recycle the same waveform. The four algorithms are paired on the same trial. 24 independent continuous sequences last 24 s each. Tracking is balanced across four scenes and nominal SNR -10, -5, 0 dB. There are 120 new sensitivity trials, each evaluated under four paired conditions. Quick mode is an engineering smoke check and is not combined with full mode. Parameters were fixed before the full run; there is no test-driven parameter search.

SeedSequence entropy is `[20261002, split, scene_index, ...]`; exact per-trial lists are stored in NPZ metadata, CSV and `data/synthetic/full/manifest.jsonl`. Split codes are 1 validation negatives, 2 test negatives, 3 test positives, 4 sensitivity, 5 tracking, 6 bootstrap, 77 sensor perturbations, 90 self-test. Static positive suffixes are `[snr_index, trial_index]`; static negative suffixes are `[trial_index]`; tracking/sensitivity suffixes are `[snr_index, repeat_index]`. Scene families are shared between calibration and test but realized physical scenes are independent; this is not a held-out-environment or held-out-drone experiment.

## Coordinate and synthesis model

Azimuth increases counterclockwise from +x; elevation is above the array plane. $u(a,e)=(\cos e\cos a,\cos e\sin a,\sin e)$. Eight microphones use the exact coordinates in `config.json`; diameter is 0.394671 m. The array is planar, so an upper-hemisphere prior is essential; it cannot resolve the lower/upper mirror ambiguity. The search includes a single zenith point and full azimuth coverage. Zenith azimuth is intrinsically undefined; spherical error is the principal metric and raw wrapped azimuth errors are also disclosed. True static directions are uniform in azimuth and in sine elevation (uniform solid angle on the upper hemisphere).

A source waveform is synthesized at 24 kHz, then evaluated at fractional arrival times by linear interpolation to 8 kHz. For microphone $m$, $x_m(t)=g_m[d_m(t)+r_m(t)+n_m(t)]$ conceptually, with each contribution's normalization implemented explicitly in `simulate`. Direct source delay is $\tau_m(t)=(\|R(t)u(t)-p_m^{actual}\|-R(t))/c+\delta_m$. Propagation uses spherical distances and relative amplitude $R/\|Ru-p_m\|$. Actual sound speed is uniform 338–348 m/s; steering assumes 343 m/s. Per-channel gains are log-normal with Gaussian 0.6 dB standard deviation. Nominal geometry/delay perturbations are zero; sensitivity adds Gaussian xyz offsets (including z) and Gaussian fixed channel time offsets. Different generation and steering models reduce the most direct inverse crime, but do not establish real-world validity.

The multirotor-like signal sums four oscillators. A nominal base is uniform 85–230 Hz. Each rotor has a Gaussian relative offset SD 0.012 and sinusoidal frequency modulation of relative depth uniform 0.008–0.025, rate 0.6–2 Hz and random phase. Harmonic phases are independent; amplitudes are uniform(0.6,1.4)/$k^{0.65}$, for $k=1,\ldots,\min(15,\lfloor3200/(1.07f_0)\rfloor)$. Unit-RMS tonal and 120–3200 Hz third-order Butterworth-filtered Gaussian broadband parts have nominal tonal power fraction uniform 0.55–0.85 before their combination and final normalization. A sinusoidal amplitude envelope has depth 0.12 and frequency 0.3–1.5 Hz. This phenomenological model is not a validated aircraft sound-emission model.

A weak echo has RMS ratio uniform 0.05–0.25 relative to the direct target, delay 3–12 ms, azimuth offset 25–80 degrees and elevation max(5 degrees,0.65 times target elevation). It is a synthetic secondary path, not a physically ray-traced outdoor ground reflection. The target direct-path mean-square power across all microphones divided by total nuisance power defines SNR; the echo is excluded from the SNR numerator and nuisance denominator. Exact achieved per-frame SNR is saved. There is no source-level calibration, atmospheric absorption model, exact retarded-time solution, moving-source Doppler validation, or distance-to-SNR conversion.

Nuisance scenes: (1) independent unit Gaussian sensor noise; (2) 0.35 times sensor noise plus independent 180 Hz second-order low-pass noise per channel, plus 0.25 times a shared 90 Hz low-pass component, normalized before mixing; (3) 0.6 times sensor noise plus a directional 160–3200 Hz third-order band-pass noise source; (4) 0.6 times sensor noise plus a directional one-oscillator engine-like harmonic confounder. Engine base/offset distributions overlap the target; its modulation depth is 0.001–0.004 and harmonic fraction 0.82–0.95. Nuisance direction is uniform azimuth and elevation 0–65 degrees; range is uniform 10–60 m. No minimum target/interferer angular separation is imposed. The wind model is colored correlated noise, not measured atmospheric turbulence. Engine negatives are deliberately difficult: harmonicity and spatial coherence do not identify drone class.

## Spectral front end, estimated base and detector

Frames are disjoint 1600-sample (0.2 s) blocks at 8 kHz: output cadence 5 Hz. Each channel is demeaned over the frame. Five 512-point periodic-Hann segments, hop 256, start at samples 0,256,512,768,1024; the remaining 64 samples enter the full-frame harmonic estimator but not the Welch estimate. For pair $i<j$, $G_{ij}(f)=\frac15\sum_\ell X_{i\ell}(f)X_{j\ell}^*(f)$ and $P_i(f)=\frac15\sum_\ell|X_{i\ell}(f)|^2$. Define $\gamma_{ij}^2=\mathrm{clip}(|G_{ij}|^2/(P_iP_j+10^{-20}),0,1)$ and $Q_{ij}=G_{ij}/\max(|G_{ij}|,10^{-20})$. This is a finite-sample Welch magnitude-squared coherence estimate; overlap reduces effective sample count and no unbiased-coherence claim is made. It is not computed from a single snapshot, which would give trivial coherence.

An additional 2048-point real FFT of the entire periodic-Hann-windowed frame is used for harmonic evidence; zero-padding interpolates spectral samples but does not improve the physical 5 Hz window resolution. Average the eight channel powers into $P(f)$. Let $M(f)$ be a 31-bin local median, nearest-edge padding, and $L(f)=\log(1+P(f)/\max(M(f),10^{-20}))-\log2$. Smooth $L$ with a Gaussian of SD one FFT bin (SciPy default reflect edges). For $b\in\{80,82,\ldots,240\}$ Hz, evaluate $J(b)=\sum_{k=1}^{12}k^{-1/2}L(\operatorname{round}(kb\cdot2048/8000))/\sum_{k=1}^{12}k^{-1/2}$. The argument denotes a nearest FFT-bin index, not interpolation. $\hat f_0=\arg\max_b J(b)$; ties use the first candidate. There is no true-base input. Absolute percentage error against the generator's nominal base is a diagnostic only: median 1.3475% across all positive test trials. Four perturbed rotors do not possess one exact common instantaneous base.

Within the 200–3000 Hz band, $d(f)=|f-\operatorname{round}(f/\hat f_0)\hat f_0|$, $\sigma(f)=\max(8,0.012f)$ Hz, and $H(f)=0.1+0.9\exp[-d(f)^2/(2\sigma(f)^2)]$. $H=0$ outside the band. On the 512-point FFT grid the retained bins actually run from 203.125 to 3000 Hz. The floor retains broadband evidence. Detection score is $D=\max(0,J(\hat f_0))[0.25+\sum_{i<j,f}H(f)\gamma_{ij}^2(f)/(28\sum_fH(f))]$. One common detector is used for all four localizers: detection results must not be presented as four different trained detectors.

Only independent validation-negative scores set the threshold. Sort $n=800$ scores, take order statistic $k=\lceil(n+1)(1-0.05)\rceil=761$ (1-based), and declare detection iff $D>\theta$. The fitted threshold is **1.88801202519**, validation empirical FPR **0.048750**. Equal-scene stratification targets this explicit nuisance mixture. The order-statistic rule is inspired by finite-sample calibration, but stratified non-identical draws mean no universal distribution-free or per-scene 5% guarantee is asserted. There is no positive-label fitting, test-threshold adjustment or double-threshold hysteresis. Engine-specific false alarms may exceed 5% even when aggregate FPR does not.

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

Tracking summary values are equal-weight means of per-sequence metrics, with 2000 whole-sequence bootstrap samples for means and paired raw-minus-smoothed errors. Frames, STFT windows and overlapping detection windows are never bootstrap units. Fewer than two independent units provide no informative bootstrap interval: `bootstrap_mean` returns `[None, None]` (JSON `[null, null]`), including a one-sequence quick gated subset. Gated conditional-error averages use only sequences with available output; their counts and coverage are explicitly reported, and no favorable comparison is inferred from dropping unavailable sequences. In this run the combined gate produces any positive-period output in only 6 of 24 sequences. Any available conditional bootstrap interval is weak evidence about this selected subset and is not generalized to missed sequences or real flight populations. The `p95_deg` tracking aggregate is the mean of within-sequence p95s, not a pooled p95. First-detection latency is measured at the end of the first positive detected frame relative to target onset; sequences never detected are counted and omitted only from the conditional latency average.

## Observed primary outcomes and limits

Test recall is **0.035000**, false-alarm rate **0.056000**, and balanced accuracy **0.489500**. Descriptive test ROC AUC is **0.734512** (no AUC CI is claimed); equal-score groups enter the curve together and trapezoidal integration handles ties. ROC thresholds use inclusive score comparisons, and the independently frozen strict-threshold operating point is separately marked. The ROC is descriptive only and selects no deployment threshold. Unconditional mean spherical errors are PHAT **24.8408 deg**, coherence **25.1229 deg**, harmonic **26.2207 deg**, combined **26.5529 deg**. These are measured program outputs, not expected/theoretical or fabricated values. The tables below disclose all SNR/scene cells, tails, conditional failures and independent-sequence results. A combination must not be described as superior when its paired intervals/point estimates do not support that statement. Harmonic confounders, coherent distractors and planar-array elevation conditioning are structural limitations of this simple method, not test exclusions.

Host: **12th Gen Intel(R) Core(TM) i7-12700KF**, Windows-11-10.0.26300-SP0. Python 3.12.14, one thread requested through OpenBLAS/OMP/MKL/NumExpr environment variables and SciPy FFT workers=1. Timings use `perf_counter_ns` over a shared front end (including the detector and estimated base) plus one method's search. Geometry construction (0.003053 s), warm-up, signal generation, disk I/O, plotting and the 200 ms acquisition window are excluded. Per-method timings share the same front end; their sum double counts it. Compute throughput is not acquisition/output cadence, nor end-to-end device performance. Window plus p95 is the nominal 200 ms frame fill plus measured p95 compute, excluding hardware/buffering/transport/display. Workstation background load and process scheduling were not isolated. The benchmark does not certify the organizer's target hardware.

## Artifacts and reproduction

- `code/experiment.py --self-test`: runnable assertions for wrap/zenith/antipodal metrics, calibration rank, known-direction localization, deterministic synthesis, exact SNR, steering sign, causal wrap and bounded hold. Actual self-test record: `results/self_test.json`.
- `code/experiment.py --quick` and `--full`: full pipeline with separate outputs. Completed runs are protected from silent overwrite. Move their output folders intentionally to rerun.
- `code/summarize_experiment.py results/full`: rebuild reports/tables/figures from saved CSV without rerunning acoustics.
- `code/requirements-lock.txt`: exact installed Python 3.12 package versions. Dependencies used locally are in `.python-packages`; the script inserts that directory only under Python 3.12 to avoid loading incompatible NumPy wheels into 3.10.
- All static validation/test/sensitivity audio, not just examples, is float32 in `data/synthetic/full/validation`, `test`, `sensitivity`; filenames are trial IDs, sample-major shape (1600,8), unscaled mixtures. Seed tuples, actual geometry/delays, sample rate, frame truth and nominal array are embedded. Continuous tracking recordings are saved under `sequences`; a representative sequence and each static nuisance/label example additionally have 8-channel PCM16 WAV copies and scale sidecars.
- `test_frames.csv`, `sensitivity_frames.csv`, `tracking_frames.csv` contain raw per-frame/per-method outputs; repeated static method rows are paired observations, not independent trials. `validation_negatives.csv` contains every calibration score. `manifest.jsonl`, `config.json`, `runtime_environment.json`, `summary.json`, `source_manifest.json` and SHA256 `artifact_manifest.json` support inspection and reconstruction. The latter hashes all experiment scripts, lock/readme, full result files, all synthetic recordings and generated figures (excluding its own self-reference). `verify_experiment.py` verifies the executed source hash, every listed artifact, exact counts, preserved gate/miss semantics and eight prespecified bit-exact waveform/estimator reconstructions. The saved `quick` folder is a prior engineering checkpoint with its own earlier source hash, not the final scientific run; its conditional intervals are not publication evidence.
- Figure pairs (7-inch source width, 300 dpi PNG, vector PDF): `array_and_spectrum`, `detection`, `detection_roc`, `localization`, `paired_improvements`, `tracking`, `sensitivity`, `acoustic_maps` under `figures/full`. The example sequence is fixed by ID before evaluating results, not chosen for successful tracking. Acoustic maps use preselected test trial `pos-2-2-0` (directional broadband nuisance, -5 dB, replicate 0); all 3601 grid responses, including the single zenith, are in `acoustic_maps_fixed_trial.npz`, with peak azimuth/elevation in `acoustic_map_peaks.csv`. The map image shows the rectangular 0–87-degree elevation grid; a possible zenith peak is marked at 90 degrees. White x marks the target, orange circle the estimate and orange triangle the nuisance direction.

## Prior-method attribution for the manuscript author

The supplied Chen, Chen and Wang (2022) review, DOI 10.12141/j.issn.1000-565X.220277, establishes the broader TDOA/GCC, harmonic UAV acoustics and array background. The present equations are a particular reproducible implementation, not a reproduction of every published variant. Conventional SRP sums generalized pair correlations at geometric delays; see the primary article [Source Localization with Acoustic Sensor Arrays Using Generative Model Based Fitting with Sparse Constraints](https://pmc.ncbi.nlm.nih.gov/articles/PMC3545592/). The Welch coherence definition is documented by [SciPy 1.15.3](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.signal.coherence.html), citing Welch (1967). The manuscript should use its independently verified primary references for SRP-PHAT and drone harmonic localization; a new implementation is not evidence of methodological priority.

## Detection (rates, not percentages)

| group | positive_n | negative_n | tp | fp | tpr | fpr | balanced_accuracy | balanced_accuracy_ci95 |
|---|---|---|---|---|---|---|---|---|
| all | 1000 | 1000 | 35 | 56 | 0.0350 | 0.0560 | 0.4895 | [0.481, 0.4975] |
| snr=-15 | 200 | 1000 | 8 | 56 | 0.0400 | 0.0560 | 0.4920 | [0.47848749999999995, 0.5075] |
| snr=-10 | 200 | 1000 | 2 | 56 | 0.0100 | 0.0560 | 0.4770 | [0.46799999999999997, 0.4875] |
| snr=-5 | 200 | 1000 | 0 | 56 | 0.0000 | 0.0560 | 0.4720 | [0.4655, 0.4785] |
| snr=0 | 200 | 1000 | 1 | 56 | 0.0050 | 0.0560 | 0.4745 | [0.4665, 0.4825] |
| snr=5 | 200 | 1000 | 24 | 56 | 0.1200 | 0.0560 | 0.5320 | [0.51, 0.5555] |
| sensor_noise | 250 | 250 | 0 | 0 | 0.0000 | 0.0000 | 0.5000 | [0.5, 0.5] |
| wind | 250 | 250 | 6 | 0 | 0.0240 | 0.0000 | 0.5120 | [0.504, 0.522] |
| directional | 250 | 250 | 4 | 0 | 0.0160 | 0.0000 | 0.5080 | [0.502, 0.516] |
| engine | 250 | 250 | 25 | 56 | 0.1000 | 0.2240 | 0.4380 | [0.408, 0.468] |

## Unconditional and detected-only localization

| method | group | n | mean_deg | median_deg | p95_deg | azimuth_mae_deg | elevation_mae_deg | detected_n | detected_mean_deg | joint_detection_within10_rate |
|---|---|---|---|---|---|---|---|---|---|---|
| phat | all | 1000 | 24.8408 | 2.7739 | 114.2556 | 28.9674 | 8.8574 | 35 | 22.5075 | 0.0240 |
| phat | snr=-15 | 200 | 38.6829 | 22.6901 | 117.2460 | 45.3235 | 13.9818 | 8 | 61.7084 | 0.0000 |
| phat | snr=-10 | 200 | 39.9899 | 12.0755 | 126.3394 | 44.6937 | 13.6835 | 2 | 118.9702 | 0.0000 |
| phat | snr=-5 | 200 | 25.7785 | 2.6173 | 115.7745 | 31.8644 | 7.7935 | 0 | NA | 0.0000 |
| phat | snr=0 | 200 | 17.8075 | 1.9949 | 95.9106 | 22.0612 | 7.1223 | 1 | 2.0807 | 0.0050 |
| phat | snr=5 | 200 | 1.9451 | 1.3282 | 5.7294 | 0.8940 | 1.7058 | 24 | 2.2530 | 0.1150 |
| phat | sensor_noise | 250 | 5.5391 | 2.4091 | 16.9483 | 3.8477 | 4.1808 | 0 | NA | 0.0000 |
| phat | wind | 250 | 1.9157 | 1.4045 | 5.6124 | 0.9266 | 1.6517 | 6 | 1.7653 | 0.0240 |
| phat | directional | 250 | 54.5031 | 54.0787 | 124.0920 | 66.4253 | 18.0042 | 4 | 5.1409 | 0.0120 |
| phat | engine | 250 | 37.4053 | 4.5278 | 127.7493 | 44.6699 | 11.5928 | 25 | 30.2642 | 0.0600 |
| phat | sensor_noise:-15 | 50 | 17.3133 | 9.4854 | 58.6379 | 14.3583 | 11.7390 | 0 | NA | 0.0000 |
| phat | sensor_noise:-10 | 50 | 4.1551 | 3.1468 | 11.0021 | 1.8939 | 3.7417 | 0 | NA | 0.0000 |
| phat | sensor_noise:-5 | 50 | 2.1917 | 1.4061 | 6.7286 | 1.3259 | 1.8371 | 0 | NA | 0.0000 |
| phat | sensor_noise:0 | 50 | 1.9160 | 1.8685 | 3.8618 | 0.7547 | 1.7231 | 0 | NA | 0.0000 |
| phat | sensor_noise:5 | 50 | 2.1194 | 1.4820 | 6.0972 | 0.9055 | 1.8630 | 0 | NA | 0.0000 |
| phat | wind:-15 | 50 | 2.1152 | 1.6844 | 5.8761 | 1.2102 | 1.7626 | 0 | NA | 0.0000 |
| phat | wind:-10 | 50 | 2.1015 | 1.4183 | 6.8541 | 0.9176 | 1.8710 | 0 | NA | 0.0000 |
| phat | wind:-5 | 50 | 1.9286 | 1.4682 | 4.6466 | 0.9545 | 1.6580 | 0 | NA | 0.0000 |
| phat | wind:0 | 50 | 1.6482 | 1.2794 | 4.7405 | 0.8685 | 1.3685 | 0 | NA | 0.0000 |
| phat | wind:5 | 50 | 1.7849 | 1.2707 | 4.6726 | 0.6824 | 1.5983 | 6 | 1.7653 | 0.1200 |
| phat | directional:-15 | 50 | 65.2736 | 66.4666 | 123.1781 | 79.4421 | 20.0857 | 0 | NA | 0.0000 |
| phat | directional:-10 | 50 | 73.9235 | 70.9896 | 135.2400 | 83.1155 | 24.0788 | 0 | NA | 0.0000 |
| phat | directional:-5 | 50 | 65.2837 | 60.1956 | 137.5057 | 82.5872 | 20.1306 | 0 | NA | 0.0000 |
| phat | directional:0 | 50 | 65.6817 | 68.4477 | 113.3018 | 85.6748 | 23.7011 | 0 | NA | 0.0000 |
| phat | directional:5 | 50 | 2.3528 | 1.4559 | 7.7309 | 1.3068 | 2.0248 | 4 | 5.1409 | 0.0600 |
| phat | engine:-15 | 50 | 70.0298 | 63.6806 | 129.3192 | 86.2836 | 22.3398 | 8 | 61.7084 | 0.0000 |
| phat | engine:-10 | 50 | 79.7793 | 76.3815 | 140.0066 | 92.8478 | 25.0422 | 2 | 118.9702 | 0.0000 |
| phat | engine:-5 | 50 | 33.7099 | 2.6556 | 123.0263 | 42.5899 | 7.5482 | 0 | NA | 0.0000 |
| phat | engine:0 | 50 | 1.9841 | 1.3457 | 4.7233 | 0.9467 | 1.6966 | 1 | 2.0807 | 0.0200 |
| phat | engine:5 | 50 | 1.5233 | 1.0310 | 4.2977 | 0.6814 | 1.3370 | 14 | 1.6370 | 0.2800 |
| coherence | all | 1000 | 25.1229 | 2.9410 | 110.9920 | 29.3833 | 8.9534 | 35 | 22.8218 | 0.0240 |
| coherence | snr=-15 | 200 | 37.3644 | 18.7855 | 116.4224 | 44.4692 | 13.3021 | 8 | 61.8038 | 0.0000 |
| coherence | snr=-10 | 200 | 39.9238 | 10.4598 | 126.3394 | 44.7205 | 13.6138 | 2 | 118.9702 | 0.0000 |
| coherence | snr=-5 | 200 | 28.5139 | 2.9542 | 115.7745 | 34.7927 | 8.9506 | 0 | NA | 0.0000 |
| coherence | snr=0 | 200 | 17.8039 | 1.9904 | 95.9106 | 22.0252 | 7.1391 | 1 | 2.0807 | 0.0050 |
| coherence | snr=5 | 200 | 2.0086 | 1.3380 | 6.8292 | 0.9090 | 1.7613 | 24 | 2.6796 | 0.1150 |
| coherence | sensor_noise | 250 | 4.4558 | 2.3363 | 12.8010 | 3.2002 | 3.5788 | 0 | NA | 0.0000 |
| coherence | wind | 250 | 1.9142 | 1.3603 | 5.3789 | 0.8694 | 1.6729 | 6 | 2.2618 | 0.0240 |
| coherence | directional | 250 | 54.5106 | 53.8372 | 124.0920 | 66.4373 | 17.9965 | 4 | 5.1409 | 0.0120 |
| coherence | engine | 250 | 39.6111 | 8.6545 | 127.7493 | 47.0265 | 12.5654 | 25 | 30.5851 | 0.0600 |
| coherence | sensor_noise:-15 | 50 | 12.1491 | 7.2743 | 43.4144 | 11.1096 | 9.0278 | 0 | NA | 0.0000 |
| coherence | sensor_noise:-10 | 50 | 3.8748 | 3.3400 | 9.0516 | 1.8796 | 3.4219 | 0 | NA | 0.0000 |
| coherence | sensor_noise:-5 | 50 | 2.1976 | 1.3820 | 6.2236 | 1.3581 | 1.8364 | 0 | NA | 0.0000 |
| coherence | sensor_noise:0 | 50 | 1.8662 | 1.5922 | 4.3686 | 0.7479 | 1.6702 | 0 | NA | 0.0000 |
| coherence | sensor_noise:5 | 50 | 2.1911 | 1.4820 | 6.8972 | 0.9055 | 1.9375 | 0 | NA | 0.0000 |
| coherence | wind:-15 | 50 | 2.0249 | 1.6562 | 5.7623 | 1.0416 | 1.7550 | 0 | NA | 0.0000 |
| coherence | wind:-10 | 50 | 2.0866 | 1.3643 | 6.7044 | 0.8591 | 1.8752 | 0 | NA | 0.0000 |
| coherence | wind:-5 | 50 | 1.9664 | 1.4229 | 4.7322 | 0.8945 | 1.7073 | 0 | NA | 0.0000 |
| coherence | wind:0 | 50 | 1.6485 | 1.2794 | 4.7405 | 0.8694 | 1.3685 | 0 | NA | 0.0000 |
| coherence | wind:5 | 50 | 1.8444 | 1.2707 | 5.6124 | 0.6824 | 1.6583 | 6 | 2.2618 | 0.1200 |
| coherence | directional:-15 | 50 | 65.2389 | 66.4666 | 123.1781 | 79.4421 | 20.0257 | 0 | NA | 0.0000 |
| coherence | directional:-10 | 50 | 74.0498 | 71.9375 | 135.2400 | 83.2355 | 24.1157 | 0 | NA | 0.0000 |
| coherence | directional:-5 | 50 | 65.2837 | 60.1956 | 137.5057 | 82.5872 | 20.1306 | 0 | NA | 0.0000 |
| coherence | directional:0 | 50 | 65.6610 | 68.4477 | 113.3018 | 85.5548 | 23.7611 | 0 | NA | 0.0000 |
| coherence | directional:5 | 50 | 2.3197 | 1.4559 | 7.7309 | 1.3668 | 1.9492 | 4 | 5.1409 | 0.0600 |
| coherence | engine:-15 | 50 | 70.0446 | 63.6806 | 129.3192 | 86.2836 | 22.3998 | 8 | 61.8038 | 0.0000 |
| coherence | engine:-10 | 50 | 79.6839 | 76.3815 | 140.0066 | 92.9078 | 25.0422 | 2 | 118.9702 | 0.0000 |
| coherence | engine:-5 | 50 | 44.6078 | 8.4677 | 123.0263 | 54.3309 | 12.1280 | 0 | NA | 0.0000 |
| coherence | engine:0 | 50 | 2.0398 | 1.3840 | 4.9136 | 0.9288 | 1.7566 | 1 | 2.0807 | 0.0200 |
| coherence | engine:5 | 50 | 1.6792 | 1.0775 | 5.1383 | 0.6814 | 1.5003 | 14 | 2.1554 | 0.2800 |
| harmonic | all | 1000 | 26.2207 | 3.0800 | 114.1791 | 30.4455 | 9.3879 | 35 | 22.8604 | 0.0240 |
| harmonic | snr=-15 | 200 | 38.7402 | 23.0859 | 117.2460 | 45.4569 | 13.8081 | 8 | 61.8038 | 0.0000 |
| harmonic | snr=-10 | 200 | 40.2046 | 14.9381 | 126.3394 | 44.7807 | 13.8467 | 2 | 118.9702 | 0.0000 |
| harmonic | snr=-5 | 200 | 34.4029 | 4.7964 | 119.2613 | 42.6186 | 10.7448 | 0 | NA | 0.0000 |
| harmonic | snr=0 | 200 | 15.7359 | 1.7760 | 92.8660 | 18.4653 | 6.7530 | 1 | 2.0807 | 0.0050 |
| harmonic | snr=5 | 200 | 2.0200 | 1.3462 | 6.2799 | 0.9061 | 1.7870 | 24 | 2.7359 | 0.1150 |
| harmonic | sensor_noise | 250 | 5.7021 | 2.3558 | 20.1554 | 4.0389 | 4.0980 | 0 | NA | 0.0000 |
| harmonic | wind | 250 | 1.9648 | 1.3988 | 5.6833 | 0.9353 | 1.6960 | 6 | 2.2618 | 0.0240 |
| harmonic | directional | 250 | 52.8571 | 52.0190 | 124.0920 | 63.5476 | 17.7511 | 4 | 6.5540 | 0.0120 |
| harmonic | engine | 250 | 44.3589 | 29.9878 | 130.2654 | 53.2603 | 14.0067 | 25 | 30.4131 | 0.0600 |
| harmonic | sensor_noise:-15 | 50 | 17.3514 | 7.9283 | 63.0168 | 14.9507 | 10.7406 | 0 | NA | 0.0000 |
| harmonic | sensor_noise:-10 | 50 | 4.8332 | 2.9176 | 14.5224 | 2.1651 | 4.2610 | 0 | NA | 0.0000 |
| harmonic | sensor_noise:-5 | 50 | 2.2395 | 1.6396 | 6.3178 | 1.3805 | 1.8654 | 0 | NA | 0.0000 |
| harmonic | sensor_noise:0 | 50 | 1.8491 | 1.5579 | 3.9518 | 0.7859 | 1.6398 | 0 | NA | 0.0000 |
| harmonic | sensor_noise:5 | 50 | 2.2372 | 1.4820 | 6.5778 | 0.9124 | 1.9830 | 0 | NA | 0.0000 |
| harmonic | wind:-15 | 50 | 2.3705 | 1.9203 | 5.7885 | 1.2713 | 2.0062 | 0 | NA | 0.0000 |
| harmonic | wind:-10 | 50 | 2.1730 | 1.4162 | 7.0572 | 0.9345 | 1.9446 | 0 | NA | 0.0000 |
| harmonic | wind:-5 | 50 | 1.9228 | 1.4229 | 4.7970 | 0.9157 | 1.6446 | 0 | NA | 0.0000 |
| harmonic | wind:0 | 50 | 1.4976 | 1.2580 | 3.8605 | 0.8694 | 1.2102 | 0 | NA | 0.0000 |
| harmonic | wind:5 | 50 | 1.8600 | 1.3027 | 5.6124 | 0.6858 | 1.6742 | 6 | 2.2618 | 0.1200 |
| harmonic | directional:-15 | 50 | 65.2457 | 66.4666 | 123.1781 | 79.3821 | 20.0857 | 0 | NA | 0.0000 |
| harmonic | directional:-10 | 50 | 73.9235 | 70.9896 | 135.2400 | 83.1755 | 24.0188 | 0 | NA | 0.0000 |
| harmonic | directional:-5 | 50 | 65.2813 | 60.1956 | 136.5283 | 82.7072 | 20.2506 | 0 | NA | 0.0000 |
| harmonic | directional:0 | 50 | 57.4469 | 54.3794 | 106.9561 | 71.1730 | 22.3183 | 0 | NA | 0.0000 |
| harmonic | directional:5 | 50 | 2.3882 | 1.4793 | 7.4137 | 1.3001 | 2.0822 | 4 | 6.5540 | 0.0600 |
| harmonic | engine:-15 | 50 | 69.9931 | 63.6806 | 129.3192 | 86.2236 | 22.3998 | 8 | 61.8038 | 0.0000 |
| harmonic | engine:-10 | 50 | 79.8885 | 76.1717 | 140.0066 | 92.8478 | 25.1622 | 2 | 118.9702 | 0.0000 |
| harmonic | engine:-5 | 50 | 68.1680 | 74.4104 | 130.8116 | 85.4712 | 19.2187 | 0 | NA | 0.0000 |
| harmonic | engine:0 | 50 | 2.1501 | 1.3840 | 4.7233 | 1.0330 | 1.8439 | 1 | 2.0807 | 0.0200 |
| harmonic | engine:5 | 50 | 1.5947 | 1.0310 | 4.5417 | 0.7261 | 1.4087 | 14 | 1.8482 | 0.2800 |
| combined | all | 1000 | 26.5529 | 3.3045 | 114.5368 | 30.8621 | 9.4180 | 35 | 22.8604 | 0.0240 |
| combined | snr=-15 | 200 | 38.6989 | 21.9051 | 117.5236 | 46.1033 | 13.5821 | 8 | 61.8038 | 0.0000 |
| combined | snr=-10 | 200 | 40.1297 | 13.0122 | 126.3394 | 44.7364 | 13.8135 | 2 | 118.9702 | 0.0000 |
| combined | snr=-5 | 200 | 35.4832 | 5.6959 | 119.2613 | 43.7252 | 11.2915 | 0 | NA | 0.0000 |
| combined | snr=0 | 200 | 16.4581 | 1.9071 | 95.8662 | 18.8461 | 6.6417 | 1 | 2.0807 | 0.0050 |
| combined | snr=5 | 200 | 1.9944 | 1.3380 | 6.3907 | 0.8994 | 1.7611 | 24 | 2.7359 | 0.1150 |
| combined | sensor_noise | 250 | 5.5015 | 2.2570 | 16.2084 | 4.5427 | 3.7905 | 0 | NA | 0.0000 |
| combined | wind | 250 | 1.9955 | 1.3988 | 5.6994 | 0.8982 | 1.7341 | 6 | 2.2618 | 0.0240 |
| combined | directional | 250 | 51.8034 | 50.1405 | 123.9486 | 61.8886 | 17.4937 | 4 | 6.5540 | 0.0120 |
| combined | engine | 250 | 46.9111 | 40.5464 | 131.1203 | 56.1188 | 14.6536 | 25 | 30.4131 | 0.0600 |
| combined | sensor_noise:-15 | 50 | 17.1209 | 7.4132 | 67.2099 | 17.5476 | 9.8961 | 0 | NA | 0.0000 |
| combined | sensor_noise:-10 | 50 | 4.2910 | 3.4620 | 12.1979 | 1.9276 | 3.8090 | 0 | NA | 0.0000 |
| combined | sensor_noise:-5 | 50 | 2.1502 | 1.4454 | 6.0796 | 1.5678 | 1.7654 | 0 | NA | 0.0000 |
| combined | sensor_noise:0 | 50 | 1.8078 | 1.4288 | 4.3686 | 0.7650 | 1.6157 | 0 | NA | 0.0000 |
| combined | sensor_noise:5 | 50 | 2.1373 | 1.3945 | 6.5778 | 0.9055 | 1.8661 | 0 | NA | 0.0000 |
| combined | wind:-15 | 50 | 2.3525 | 1.9043 | 6.0835 | 1.2000 | 2.0066 | 0 | NA | 0.0000 |
| combined | wind:-10 | 50 | 2.2401 | 1.4340 | 6.1566 | 0.8745 | 2.0239 | 0 | NA | 0.0000 |
| combined | wind:-5 | 50 | 1.9739 | 1.4229 | 4.7970 | 0.8472 | 1.7113 | 0 | NA | 0.0000 |
| combined | wind:0 | 50 | 1.5624 | 1.2580 | 4.7405 | 0.8760 | 1.2702 | 0 | NA | 0.0000 |
| combined | wind:5 | 50 | 1.8486 | 1.2707 | 5.6124 | 0.6935 | 1.6583 | 6 | 2.2618 | 0.1200 |
| combined | directional:-15 | 50 | 65.2457 | 66.4666 | 123.1781 | 79.3821 | 20.0857 | 0 | NA | 0.0000 |
| combined | directional:-10 | 50 | 74.0048 | 71.9375 | 135.2400 | 83.2355 | 24.0788 | 0 | NA | 0.0000 |
| combined | directional:-5 | 50 | 65.2449 | 60.1956 | 136.5283 | 82.7072 | 20.1306 | 0 | NA | 0.0000 |
| combined | directional:0 | 50 | 52.0646 | 48.2468 | 104.4786 | 62.8457 | 21.0022 | 0 | NA | 0.0000 |
| combined | directional:5 | 50 | 2.4572 | 1.4793 | 7.4137 | 1.2724 | 2.1714 | 4 | 6.5540 | 0.0600 |
| combined | engine:-15 | 50 | 70.0763 | 63.6278 | 129.3192 | 86.2836 | 22.3398 | 8 | 61.8038 | 0.0000 |
| combined | engine:-10 | 50 | 79.9827 | 76.1717 | 140.0066 | 92.9078 | 25.3422 | 2 | 118.9702 | 0.0000 |
| combined | engine:-5 | 50 | 72.5639 | 77.5097 | 130.8116 | 89.7788 | 21.5586 | 0 | NA | 0.0000 |
| combined | engine:0 | 50 | 10.3976 | 1.7050 | 74.9762 | 10.8977 | 2.6785 | 1 | 2.0807 | 0.0200 |
| combined | engine:5 | 50 | 1.5347 | 1.0310 | 4.2977 | 0.7261 | 1.3487 | 14 | 1.8482 | 0.2800 |

## Paired localization improvements (positive is better than PHAT)

| method | group | n | baseline_minus_method_mean_deg | ci95_low | ci95_high |
|---|---|---|---|---|---|
| coherence | all | 1000 | -0.2821 | -0.7706 | 0.2412 |
| coherence | snr=-15 | 200 | 1.3186 | -0.0975 | 3.2372 |
| coherence | snr=-10 | 200 | 0.0661 | -0.0835 | 0.2102 |
| coherence | snr=-5 | 200 | -2.7354 | -4.6287 | -1.1245 |
| coherence | snr=0 | 200 | 0.0036 | -0.0834 | 0.0869 |
| coherence | snr=5 | 200 | -0.0635 | -0.1348 | 0.0047 |
| coherence | sensor_noise | 250 | 1.0833 | -0.0004 | 2.6584 |
| coherence | wind | 250 | 0.0015 | -0.0819 | 0.0836 |
| coherence | directional | 250 | -0.0075 | -0.0628 | 0.0461 |
| coherence | engine | 250 | -2.2058 | -3.7687 | -0.8438 |
| harmonic | all | 1000 | -1.3799 | -2.1582 | -0.5577 |
| harmonic | snr=-15 | 200 | -0.0572 | -2.2187 | 2.3655 |
| harmonic | snr=-10 | 200 | -0.2147 | -0.5229 | 0.0547 |
| harmonic | snr=-5 | 200 | -8.6244 | -11.5834 | -5.9181 |
| harmonic | snr=0 | 200 | 2.0716 | 0.5042 | 3.9422 |
| harmonic | snr=5 | 200 | -0.0749 | -0.1703 | 0.0210 |
| harmonic | sensor_noise | 250 | -0.1630 | -2.0317 | 1.8007 |
| harmonic | wind | 250 | -0.0491 | -0.1720 | 0.0659 |
| harmonic | directional | 250 | 1.6459 | 0.3656 | 3.2147 |
| harmonic | engine | 250 | -6.9536 | -9.3845 | -4.6444 |
| combined | all | 1000 | -1.7121 | -2.6821 | -0.7207 |
| combined | snr=-15 | 200 | -0.0159 | -2.4680 | 2.6387 |
| combined | snr=-10 | 200 | -0.1398 | -0.3333 | 0.0615 |
| combined | snr=-5 | 200 | -9.7048 | -12.4943 | -6.9251 |
| combined | snr=0 | 200 | 1.3494 | -1.4697 | 4.5165 |
| combined | snr=5 | 200 | -0.0494 | -0.1369 | 0.0368 |
| combined | sensor_noise | 250 | 0.0376 | -1.9145 | 2.1345 |
| combined | wind | 250 | -0.0798 | -0.1899 | 0.0266 |
| combined | directional | 250 | 2.6996 | 1.0033 | 4.5821 |
| combined | engine | 250 | -9.5058 | -12.4356 | -6.7893 |

## Sensor-error sensitivity (positive increase is worse)

| method | condition | n | mean_deg | increase_vs_nominal_deg | ci95_low | ci95_high |
|---|---|---|---|---|---|---|
| phat | nominal | 120 | 29.8325 | 0.0000 | 0.0000 | 0.0000 |
| phat | position_5mm | 120 | 30.4533 | 0.6208 | 0.2797 | 0.9575 |
| phat | delay_20us | 120 | 30.9707 | 1.1382 | 0.4964 | 1.7826 |
| phat | both | 120 | 31.5522 | 1.7197 | 1.0696 | 2.3876 |
| coherence | nominal | 120 | 30.3333 | 0.0000 | 0.0000 | 0.0000 |
| coherence | position_5mm | 120 | 30.7268 | 0.3934 | 0.0969 | 0.6803 |
| coherence | delay_20us | 120 | 31.2806 | 0.9472 | 0.3294 | 1.5855 |
| coherence | both | 120 | 31.8764 | 1.5431 | 0.9249 | 2.1648 |
| harmonic | nominal | 120 | 32.6307 | 0.0000 | 0.0000 | 0.0000 |
| harmonic | position_5mm | 120 | 34.0715 | 1.4408 | 0.3918 | 3.2599 |
| harmonic | delay_20us | 120 | 33.6675 | 1.0368 | 0.4725 | 1.5769 |
| harmonic | both | 120 | 34.1810 | 1.5503 | 0.9442 | 2.1688 |
| combined | nominal | 120 | 33.1427 | 0.0000 | 0.0000 | 0.0000 |
| combined | position_5mm | 120 | 33.7716 | 0.6289 | 0.2673 | 0.9979 |
| combined | delay_20us | 120 | 34.0890 | 0.9463 | 0.4011 | 1.5033 |
| combined | both | 120 | 33.9431 | 0.8004 | -0.4707 | 1.7705 |

## Tracking (equal-weight means of independent sequence metrics)

| method | mode | sequences | sequences_with_output | coverage | mean_deg | p95_deg | turn_mean_deg | within10_all_positive_rate | chord_velocity_rmse_deg_s | absent_output_rate |
|---|---|---|---|---|---|---|---|---|---|---|
| phat | raw | 24 | 24 | 1.0000 | 21.5063 | 39.1558 | 21.2445 | 0.6562 | 32.2735 | 1.0000 |
| phat | smooth_all | 24 | 24 | 1.0000 | 23.0606 | 39.2267 | 21.7968 | 0.6158 | 15.3154 | 1.0000 |
| phat | gated | 24 | 6 | 0.0563 | 47.8126 | 71.5468 | 36.3936 | 0.0121 | 10.3627 | 0.1958 |
| coherence | raw | 24 | 24 | 1.0000 | 21.7788 | 39.2419 | 23.3597 | 0.6500 | 29.8670 | 1.0000 |
| coherence | smooth_all | 24 | 24 | 1.0000 | 23.3486 | 39.8833 | 23.2315 | 0.6112 | 15.1355 | 1.0000 |
| coherence | gated | 24 | 6 | 0.0563 | 47.7594 | 71.8875 | 36.3936 | 0.0121 | 10.3637 | 0.1958 |
| harmonic | raw | 24 | 24 | 1.0000 | 25.9694 | 45.7271 | 28.6371 | 0.5921 | 33.9963 | 1.0000 |
| harmonic | smooth_all | 24 | 24 | 1.0000 | 27.3530 | 46.7323 | 28.3074 | 0.5542 | 15.9194 | 1.0000 |
| harmonic | gated | 24 | 6 | 0.0563 | 61.8996 | 83.6453 | 40.8169 | 0.0029 | 14.6566 | 0.1958 |
| combined | raw | 24 | 24 | 1.0000 | 26.7588 | 45.4926 | 29.9138 | 0.5833 | 34.1531 | 1.0000 |
| combined | smooth_all | 24 | 24 | 1.0000 | 28.1315 | 46.7422 | 30.2972 | 0.5408 | 15.9658 | 1.0000 |
| combined | gated | 24 | 6 | 0.0563 | 65.5392 | 83.6564 | 71.2371 | 0.0017 | 10.3827 | 0.1958 |

### Tracking detection continuity, latency and paired intervals

| method | mode | detection_recall | detection_fpr | max_miss_s | sequences_with_detection | first_detection_delay_s | five_second_window_pass_rate |
|---|---|---|---|---|---|---|---|
| phat | raw | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| phat | smooth_all | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| phat | gated | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| coherence | raw | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| coherence | smooth_all | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| coherence | gated | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| harmonic | raw | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| harmonic | smooth_all | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| harmonic | gated | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| combined | raw | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| combined | smooth_all | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |
| combined | gated | 0.0096 | 0.0875 | 18.1583 | 5 | 8.4800 | 0.0000 |

| method | independent_sequences | mean_deg | ci95 |
|---|---|---|---|
| phat | 24 | -1.5543 | [-2.2627151535504915, -0.9050145809337856] |
| coherence | 24 | -1.5698 | [-2.26600237489922, -0.9116611975754559] |
| harmonic | 24 | -1.3836 | [-2.054306264662047, -0.7655437076327724] |
| combined | 24 | -1.3727 | [-2.0345441513389453, -0.7549251983606625] |

## Host-only processing benchmark

| method | n | median_ms | p95_ms | max_ms | compute_throughput_fps | window_plus_p95_ms |
|---|---|---|---|---|---|---|
| phat | 2000 | 3.3215 | 5.0276 | 9.1208 | 281.0500 | 205.0276 |
| coherence | 2000 | 3.0715 | 4.6061 | 9.1815 | 306.5620 | 204.6061 |
| harmonic | 2000 | 3.1431 | 4.7168 | 9.8633 | 298.8251 | 204.7168 |
| combined | 2000 | 3.1107 | 4.6669 | 10.0296 | 303.9768 | 204.6669 |

## Per-sequence results (no sequence discarded)

| sequence_id | scene | snr_db | method | mode | coverage | mean_deg | p95_deg | turn_mean_deg | within10_all_positive_rate | max_miss_s |
|---|---|---|---|---|---|---|---|---|---|---|
| seq-0-0-0 | sensor_noise | -10.0000 | phat | raw | 1.0000 | 3.4434 | 8.0964 | 2.0096 | 0.9600 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | phat | smooth_all | 1.0000 | 4.0129 | 9.3569 | 3.2387 | 0.9500 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | coherence | raw | 1.0000 | 3.2693 | 6.8138 | 2.2219 | 0.9800 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | coherence | smooth_all | 1.0000 | 4.0994 | 8.4976 | 3.7863 | 0.9600 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | harmonic | raw | 1.0000 | 4.0163 | 9.2691 | 2.2102 | 0.9600 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | harmonic | smooth_all | 1.0000 | 4.6073 | 10.6417 | 3.9070 | 0.9400 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | combined | raw | 1.0000 | 3.6222 | 7.9385 | 2.1348 | 0.9700 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | combined | smooth_all | 1.0000 | 4.4635 | 9.8055 | 3.8615 | 0.9500 | 20.0000 |
| seq-0-0-0 | sensor_noise | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | phat | raw | 1.0000 | 4.7711 | 15.2241 | 7.2511 | 0.9100 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | phat | smooth_all | 1.0000 | 5.7896 | 9.0423 | 6.0652 | 0.9500 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | coherence | raw | 1.0000 | 4.5446 | 13.4104 | 6.3687 | 0.9300 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | coherence | smooth_all | 1.0000 | 5.8034 | 9.5535 | 5.5783 | 0.9600 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | harmonic | raw | 1.0000 | 5.3525 | 16.6610 | 6.2766 | 0.8800 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | harmonic | smooth_all | 1.0000 | 5.8274 | 11.3028 | 5.4413 | 0.9300 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | combined | raw | 1.0000 | 4.4441 | 15.0264 | 6.4343 | 0.9300 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | combined | smooth_all | 1.0000 | 6.0238 | 11.2651 | 5.4823 | 0.9200 | 20.0000 |
| seq-0-0-1 | sensor_noise | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | phat | raw | 1.0000 | 1.6969 | 4.8375 | 1.2592 | 1.0000 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | phat | smooth_all | 1.0000 | 4.9324 | 6.3484 | 2.7525 | 0.9700 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | coherence | raw | 1.0000 | 1.5642 | 3.6735 | 0.9308 | 1.0000 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | coherence | smooth_all | 1.0000 | 4.9278 | 6.4631 | 2.6374 | 0.9600 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | harmonic | raw | 1.0000 | 1.7331 | 4.6367 | 1.3898 | 1.0000 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | harmonic | smooth_all | 1.0000 | 4.5972 | 6.5709 | 3.1521 | 0.9700 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | combined | raw | 1.0000 | 1.5809 | 3.3446 | 1.2538 | 1.0000 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | combined | smooth_all | 1.0000 | 4.3185 | 6.2184 | 2.8894 | 0.9900 | 20.0000 |
| seq-0-1-0 | sensor_noise | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | phat | raw | 1.0000 | 3.1301 | 6.4888 | 4.5513 | 0.9900 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | phat | smooth_all | 1.0000 | 5.6413 | 8.6259 | 6.1545 | 0.9600 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | coherence | raw | 1.0000 | 2.8538 | 6.4987 | 5.1136 | 0.9900 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | coherence | smooth_all | 1.0000 | 5.7559 | 7.7542 | 6.4516 | 0.9600 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | harmonic | raw | 1.0000 | 3.0229 | 6.1390 | 3.4752 | 1.0000 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | harmonic | smooth_all | 1.0000 | 5.4938 | 7.9038 | 4.9754 | 0.9600 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | combined | raw | 1.0000 | 2.8734 | 6.4939 | 4.4092 | 1.0000 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | combined | smooth_all | 1.0000 | 5.7422 | 7.8522 | 5.7450 | 0.9600 | 20.0000 |
| seq-0-1-1 | sensor_noise | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | phat | raw | 1.0000 | 1.4235 | 3.0175 | 1.1327 | 1.0000 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | phat | smooth_all | 1.0000 | 3.2659 | 6.6316 | 2.5705 | 0.9700 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | coherence | raw | 1.0000 | 1.4691 | 3.0201 | 1.1520 | 1.0000 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | coherence | smooth_all | 1.0000 | 3.3503 | 7.1343 | 2.4924 | 0.9600 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | harmonic | raw | 1.0000 | 1.4569 | 3.0349 | 1.0102 | 1.0000 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | harmonic | smooth_all | 1.0000 | 4.3742 | 11.0159 | 2.8679 | 0.9400 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | combined | raw | 1.0000 | 1.4860 | 3.0427 | 1.0149 | 1.0000 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | combined | smooth_all | 1.0000 | 3.9597 | 8.7530 | 2.8811 | 0.9500 | 20.0000 |
| seq-0-2-0 | sensor_noise | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | phat | raw | 1.0000 | 1.5539 | 3.7535 | 1.2228 | 1.0000 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | phat | smooth_all | 1.0000 | 4.9709 | 6.5907 | 4.1781 | 0.9600 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | coherence | raw | 1.0000 | 1.4716 | 3.6642 | 1.2228 | 1.0000 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | coherence | smooth_all | 1.0000 | 5.3148 | 6.3262 | 4.2410 | 0.9600 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | harmonic | raw | 1.0000 | 1.6151 | 3.7444 | 1.2228 | 1.0000 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | harmonic | smooth_all | 1.0000 | 5.0639 | 6.3856 | 4.2527 | 0.9600 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | combined | raw | 1.0000 | 1.4372 | 3.4740 | 1.2228 | 1.0000 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | combined | smooth_all | 1.0000 | 4.8504 | 5.9510 | 4.2414 | 0.9600 | 20.0000 |
| seq-0-2-1 | sensor_noise | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | phat | raw | 1.0000 | 1.3850 | 2.5664 | 1.5845 | 1.0000 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | phat | smooth_all | 1.0000 | 5.3061 | 10.5212 | 4.5028 | 0.9400 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | coherence | raw | 1.0000 | 1.3156 | 2.4557 | 1.5845 | 1.0000 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | coherence | smooth_all | 1.0000 | 5.3574 | 10.7139 | 4.5021 | 0.9400 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | harmonic | raw | 1.0000 | 1.4545 | 3.0287 | 1.5849 | 1.0000 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | harmonic | smooth_all | 1.0000 | 4.5291 | 6.1026 | 4.7500 | 0.9700 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | combined | raw | 1.0000 | 1.3928 | 2.5066 | 1.5849 | 1.0000 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | combined | smooth_all | 1.0000 | 4.3946 | 6.3030 | 4.7368 | 0.9800 | 20.0000 |
| seq-1-0-0 | wind | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | phat | raw | 1.0000 | 1.5084 | 3.2925 | 1.2087 | 1.0000 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | phat | smooth_all | 1.0000 | 3.1525 | 4.2553 | 2.8478 | 0.9700 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | coherence | raw | 1.0000 | 1.5507 | 3.6443 | 1.2488 | 1.0000 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | coherence | smooth_all | 1.0000 | 2.8467 | 4.1117 | 2.4164 | 0.9700 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | harmonic | raw | 1.0000 | 1.5213 | 3.2925 | 1.1881 | 1.0000 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | harmonic | smooth_all | 1.0000 | 3.0828 | 4.1804 | 3.2034 | 0.9700 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | combined | raw | 1.0000 | 1.5783 | 3.7547 | 1.2848 | 1.0000 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | combined | smooth_all | 1.0000 | 2.5924 | 4.1018 | 2.7477 | 0.9800 | 20.0000 |
| seq-1-0-1 | wind | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | phat | raw | 1.0000 | 1.1596 | 2.3531 | 0.9947 | 1.0000 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | phat | smooth_all | 1.0000 | 4.8682 | 7.1697 | 4.1373 | 0.9600 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | coherence | raw | 1.0000 | 1.1500 | 2.3531 | 0.9947 | 1.0000 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | coherence | smooth_all | 1.0000 | 4.6666 | 7.1019 | 4.1373 | 0.9700 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | harmonic | raw | 1.0000 | 1.2340 | 2.6808 | 0.9947 | 1.0000 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | harmonic | smooth_all | 1.0000 | 5.3234 | 7.4693 | 4.1372 | 0.9500 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | combined | raw | 1.0000 | 1.2088 | 2.5290 | 1.0208 | 1.0000 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | combined | smooth_all | 1.0000 | 5.0770 | 7.4099 | 4.0848 | 0.9600 | 20.0000 |
| seq-1-1-0 | wind | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | phat | raw | 1.0000 | 1.1184 | 2.0750 | 0.9440 | 1.0000 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | phat | smooth_all | 1.0000 | 4.7460 | 5.0606 | 2.9057 | 0.9600 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | coherence | raw | 1.0000 | 1.1347 | 2.2418 | 0.9440 | 1.0000 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | coherence | smooth_all | 1.0000 | 5.1585 | 7.0624 | 2.9020 | 0.9500 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | harmonic | raw | 1.0000 | 1.1134 | 1.9344 | 0.9656 | 1.0000 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | harmonic | smooth_all | 1.0000 | 4.8564 | 6.3445 | 3.0030 | 0.9600 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | combined | raw | 1.0000 | 1.1260 | 2.0750 | 0.9656 | 1.0000 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | combined | smooth_all | 1.0000 | 5.0853 | 7.1202 | 2.9294 | 0.9500 | 20.0000 |
| seq-1-1-1 | wind | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | phat | raw | 1.0000 | 1.0091 | 1.5752 | 0.8217 | 1.0000 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | phat | smooth_all | 1.0000 | 4.0836 | 4.5349 | 3.0461 | 0.9700 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | coherence | raw | 1.0000 | 1.0075 | 1.5752 | 0.8217 | 1.0000 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | coherence | smooth_all | 1.0000 | 3.7526 | 4.5131 | 3.0459 | 0.9900 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | harmonic | raw | 1.0000 | 1.0293 | 1.6933 | 0.8217 | 1.0000 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | harmonic | smooth_all | 1.0000 | 4.0244 | 4.5817 | 3.0459 | 0.9800 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | combined | raw | 1.0000 | 1.0298 | 1.6933 | 0.8217 | 1.0000 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | combined | smooth_all | 1.0000 | 3.6915 | 4.5345 | 3.0459 | 0.9900 | 20.0000 |
| seq-1-2-0 | wind | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | phat | raw | 1.0000 | 1.1528 | 2.1620 | 0.9155 | 1.0000 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | phat | smooth_all | 1.0000 | 5.6163 | 10.2476 | 3.3716 | 0.9400 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | coherence | raw | 1.0000 | 1.1218 | 2.0439 | 0.9155 | 1.0000 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | coherence | smooth_all | 1.0000 | 5.2473 | 7.4574 | 3.4783 | 0.9500 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | harmonic | raw | 1.0000 | 1.1743 | 2.1648 | 0.9155 | 1.0000 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | harmonic | smooth_all | 1.0000 | 5.5797 | 10.2762 | 3.3715 | 0.9400 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | combined | raw | 1.0000 | 1.1445 | 2.0808 | 0.9155 | 1.0000 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | combined | smooth_all | 1.0000 | 5.3704 | 9.3378 | 3.3715 | 0.9500 | 20.0000 |
| seq-1-2-1 | wind | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | phat | raw | 1.0000 | 25.4167 | 46.2394 | 28.9131 | 0.1200 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | phat | smooth_all | 1.0000 | 25.4167 | 46.2394 | 28.9131 | 0.1200 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | coherence | raw | 1.0000 | 25.4167 | 46.2394 | 28.9131 | 0.1200 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | coherence | smooth_all | 1.0000 | 25.4167 | 46.2394 | 28.9131 | 0.1200 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | harmonic | raw | 1.0000 | 25.4167 | 46.2394 | 28.9131 | 0.1200 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | harmonic | smooth_all | 1.0000 | 25.4167 | 46.2394 | 28.9131 | 0.1200 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | combined | raw | 1.0000 | 25.4167 | 46.2394 | 28.9131 | 0.1200 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | combined | smooth_all | 1.0000 | 25.4167 | 46.2394 | 28.9131 | 0.1200 | 20.0000 |
| seq-2-0-0 | directional | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | phat | raw | 1.0000 | 29.1858 | 71.3242 | 34.6843 | 0.1100 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | phat | smooth_all | 1.0000 | 29.1858 | 71.3242 | 34.6843 | 0.1100 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | coherence | raw | 1.0000 | 29.1858 | 71.3242 | 34.6843 | 0.1100 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | coherence | smooth_all | 1.0000 | 29.1858 | 71.3242 | 34.6843 | 0.1100 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | harmonic | raw | 1.0000 | 29.1858 | 71.3242 | 34.6843 | 0.1100 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | harmonic | smooth_all | 1.0000 | 29.1858 | 71.3242 | 34.6843 | 0.1100 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | combined | raw | 1.0000 | 29.1858 | 71.3242 | 34.6843 | 0.1100 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | combined | smooth_all | 1.0000 | 29.1858 | 71.3242 | 34.6843 | 0.1100 | 20.0000 |
| seq-2-0-1 | directional | -10.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | phat | raw | 1.0000 | 36.7950 | 64.4841 | 22.7975 | 0.0900 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | phat | smooth_all | 1.0000 | 36.8646 | 64.9388 | 22.8626 | 0.0900 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | coherence | raw | 1.0000 | 36.7276 | 64.4841 | 22.7975 | 0.0900 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | coherence | smooth_all | 1.0000 | 36.7966 | 64.8632 | 22.8658 | 0.0900 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | harmonic | raw | 1.0000 | 36.9529 | 65.1016 | 22.7156 | 0.0900 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | harmonic | smooth_all | 1.0000 | 37.0290 | 65.2030 | 22.7846 | 0.0900 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | combined | raw | 1.0000 | 36.8295 | 64.4849 | 22.6918 | 0.1000 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | combined | smooth_all | 1.0000 | 36.9134 | 65.2031 | 22.7674 | 0.0900 | 20.0000 |
| seq-2-1-0 | directional | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | phat | raw | 1.0000 | 46.4478 | 73.8045 | 64.7808 | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | phat | smooth_all | 1.0000 | 46.4375 | 73.8045 | 64.8657 | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | coherence | raw | 1.0000 | 46.4160 | 73.8045 | 64.6351 | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | coherence | smooth_all | 1.0000 | 46.3976 | 73.8045 | 64.7340 | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | harmonic | raw | 1.0000 | 46.4431 | 73.8045 | 64.8905 | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | harmonic | smooth_all | 1.0000 | 46.4341 | 73.8045 | 64.9761 | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | combined | raw | 1.0000 | 46.3308 | 73.8045 | 64.8705 | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | combined | smooth_all | 1.0000 | 46.3205 | 73.8045 | 64.7660 | 0.0000 | 20.0000 |
| seq-2-1-1 | directional | -5.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | phat | raw | 1.0000 | 74.8266 | 120.5934 | 112.5114 | 0.3400 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | phat | smooth_all | 1.0000 | 73.5194 | 115.3783 | 103.6089 | 0.1400 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | coherence | raw | 1.0000 | 71.1458 | 119.1869 | 100.9533 | 0.3700 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | coherence | smooth_all | 1.0000 | 70.0592 | 114.7652 | 89.7524 | 0.1800 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | harmonic | raw | 1.0000 | 73.9186 | 120.5934 | 113.4113 | 0.3500 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | harmonic | smooth_all | 1.0000 | 72.9155 | 115.6116 | 104.5231 | 0.1800 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | combined | raw | 1.0000 | 70.1206 | 118.6286 | 101.8532 | 0.3800 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | combined | smooth_all | 1.0000 | 69.3819 | 115.5126 | 90.4442 | 0.2200 | 20.0000 |
| seq-2-2-0 | directional | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | phat | raw | 1.0000 | 62.0745 | 105.3574 | 102.4218 | 0.1500 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | phat | smooth_all | 1.0000 | 61.9592 | 105.3509 | 101.8840 | 0.0500 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | phat | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | coherence | raw | 1.0000 | 59.1720 | 105.3574 | 102.4218 | 0.2000 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | coherence | smooth_all | 1.0000 | 59.0297 | 105.3484 | 101.7030 | 0.0900 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | coherence | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | harmonic | raw | 1.0000 | 65.3816 | 105.3574 | 102.4218 | 0.0800 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | harmonic | smooth_all | 1.0000 | 65.3532 | 105.3577 | 102.4346 | 0.0500 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | harmonic | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | combined | raw | 1.0000 | 60.9080 | 105.3574 | 102.4218 | 0.1800 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | combined | smooth_all | 1.0000 | 60.7182 | 105.3561 | 102.3264 | 0.0900 | 20.0000 |
| seq-2-2-1 | directional | 0.0000 | combined | gated | 0.0000 | NA | NA | NA | 0.0000 | 20.0000 |
| seq-3-0-0 | engine | -10.0000 | phat | raw | 1.0000 | 75.3934 | 109.2827 | 51.7498 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | phat | smooth_all | 1.0000 | 75.3997 | 109.2827 | 51.7508 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | phat | gated | 0.3800 | 69.7033 | 105.9714 | 53.4326 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | coherence | raw | 1.0000 | 75.3767 | 109.2827 | 51.7498 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | coherence | smooth_all | 1.0000 | 75.3826 | 109.2827 | 51.7503 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | coherence | gated | 0.3800 | 69.7033 | 105.9714 | 53.4326 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | harmonic | raw | 1.0000 | 75.3678 | 109.2827 | 51.7498 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | harmonic | smooth_all | 1.0000 | 75.3693 | 109.2827 | 51.7499 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | harmonic | gated | 0.3800 | 69.7033 | 105.9714 | 53.4326 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | combined | raw | 1.0000 | 75.3620 | 109.2827 | 51.7498 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | combined | smooth_all | 1.0000 | 75.3620 | 109.2827 | 51.7498 | 0.0000 | 4.6000 |
| seq-3-0-0 | engine | -10.0000 | combined | gated | 0.3800 | 69.7033 | 105.9714 | 53.4326 | 0.0000 | 4.6000 |
| seq-3-0-1 | engine | -10.0000 | phat | raw | 1.0000 | 89.8268 | 124.6158 | 51.9028 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | phat | smooth_all | 1.0000 | 89.8409 | 123.9133 | 51.9453 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | phat | gated | 0.3500 | 84.4809 | 107.5300 | 51.6622 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | coherence | raw | 1.0000 | 89.8804 | 124.7579 | 51.9028 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | coherence | smooth_all | 1.0000 | 89.8903 | 124.6228 | 51.9760 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | coherence | gated | 0.3500 | 84.6436 | 109.4188 | 51.6622 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | harmonic | raw | 1.0000 | 89.8901 | 124.7627 | 51.8558 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | harmonic | smooth_all | 1.0000 | 89.8977 | 124.6302 | 51.8921 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | harmonic | gated | 0.3500 | 84.6436 | 109.4188 | 51.6622 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | combined | raw | 1.0000 | 90.0020 | 124.7579 | 52.0031 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | combined | smooth_all | 1.0000 | 90.0084 | 124.7439 | 51.9938 | 0.0000 | 5.8000 |
| seq-3-0-1 | engine | -10.0000 | combined | gated | 0.3500 | 84.6436 | 109.4188 | 51.6622 | 0.0000 | 5.8000 |
| seq-3-1-0 | engine | -5.0000 | phat | raw | 1.0000 | 30.8700 | 87.6955 | 12.6822 | 0.5900 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | phat | smooth_all | 1.0000 | 30.3994 | 74.6943 | 8.6471 | 0.4900 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | phat | gated | 0.0200 | 52.2450 | 52.2986 | NA | 0.0000 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | coherence | raw | 1.0000 | 39.4553 | 94.0253 | 59.4142 | 0.4900 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | coherence | smooth_all | 1.0000 | 38.9036 | 84.1605 | 45.5994 | 0.4300 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | coherence | gated | 0.0200 | 52.2450 | 52.2986 | NA | 0.0000 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | harmonic | raw | 1.0000 | 48.7377 | 95.3181 | 95.3901 | 0.3600 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | harmonic | smooth_all | 1.0000 | 48.4173 | 91.8595 | 87.0434 | 0.2200 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | harmonic | gated | 0.0200 | 52.2450 | 52.2986 | NA | 0.0000 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | combined | raw | 1.0000 | 62.9538 | 96.1044 | 96.5438 | 0.1400 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | combined | smooth_all | 1.0000 | 62.9348 | 96.0714 | 96.3669 | 0.0000 | 20.0000 |
| seq-3-1-0 | engine | -5.0000 | combined | gated | 0.0200 | 52.2450 | 52.2986 | NA | 0.0000 | 20.0000 |
| seq-3-1-1 | engine | -5.0000 | phat | raw | 1.0000 | 16.2951 | 42.2753 | 1.1658 | 0.5800 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | phat | smooth_all | 1.0000 | 16.9161 | 41.5626 | 2.9182 | 0.5300 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | phat | gated | 0.0900 | 42.5265 | 44.0859 | NA | 0.0000 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | coherence | raw | 1.0000 | 19.7181 | 42.5694 | 17.2818 | 0.4700 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | coherence | smooth_all | 1.0000 | 19.8987 | 42.5854 | 14.6140 | 0.4500 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | coherence | gated | 0.0900 | 42.5265 | 44.0859 | NA | 0.0000 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | harmonic | raw | 1.0000 | 26.5371 | 43.0798 | 32.9051 | 0.2200 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | harmonic | smooth_all | 1.0000 | 26.5728 | 42.8866 | 32.8756 | 0.2000 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | harmonic | gated | 0.0900 | 42.5265 | 44.0859 | NA | 0.0000 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | combined | raw | 1.0000 | 26.7687 | 43.0798 | 33.0423 | 0.2100 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | combined | smooth_all | 1.0000 | 26.7934 | 42.8459 | 33.1026 | 0.2000 | 18.4000 |
| seq-3-1-1 | engine | -5.0000 | combined | gated | 0.0900 | 42.4035 | 43.8640 | NA | 0.0000 | 18.4000 |
| seq-3-2-0 | engine | 0.0000 | phat | raw | 1.0000 | 4.3165 | 35.5841 | 1.2727 | 0.9100 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | phat | smooth_all | 1.0000 | 6.2788 | 18.2858 | 1.8779 | 0.8000 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | phat | gated | 0.1000 | 22.5468 | 46.7479 | NA | 0.0400 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | coherence | raw | 1.0000 | 6.4086 | 36.3869 | 1.2690 | 0.8500 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | coherence | smooth_all | 1.0000 | 8.2551 | 25.2532 | 1.9002 | 0.7200 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | coherence | gated | 0.1000 | 22.1012 | 46.9035 | NA | 0.0400 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | harmonic | raw | 1.0000 | 19.2212 | 41.1191 | 21.5699 | 0.5100 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | harmonic | smooth_all | 1.0000 | 20.3245 | 39.6913 | 15.3222 | 0.4700 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | harmonic | gated | 0.1000 | 22.4968 | 46.6148 | NA | 0.0400 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | combined | raw | 1.0000 | 21.0756 | 41.6101 | 29.6975 | 0.4600 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | combined | smooth_all | 1.0000 | 22.1652 | 39.6911 | 27.5523 | 0.3900 | 17.0000 |
| seq-3-2-0 | engine | 0.0000 | combined | gated | 0.1000 | 22.6053 | 46.9035 | NA | 0.0400 | 17.0000 |
| seq-3-2-1 | engine | 0.0000 | phat | raw | 1.0000 | 1.3516 | 3.0408 | 1.0902 | 1.0000 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | phat | smooth_all | 1.0000 | 4.8505 | 8.2806 | 3.3945 | 0.9500 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | phat | gated | 0.4100 | 15.3729 | 72.6471 | 4.0860 | 0.2500 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | coherence | raw | 1.0000 | 1.3343 | 2.9913 | 1.0902 | 1.0000 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | coherence | smooth_all | 1.0000 | 4.8690 | 8.2618 | 3.3945 | 0.9500 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | coherence | gated | 0.4100 | 15.3369 | 72.6471 | 4.0860 | 0.2500 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | harmonic | raw | 1.0000 | 61.4884 | 143.1886 | 44.7283 | 0.5300 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | harmonic | smooth_all | 1.0000 | 62.1955 | 142.9084 | 36.0707 | 0.3900 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | harmonic | gated | 0.4100 | 99.7821 | 143.4825 | 17.3560 | 0.0300 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | combined | raw | 1.0000 | 74.3328 | 143.1886 | 76.3966 | 0.4000 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | combined | smooth_all | 1.0000 | 74.3862 | 143.0849 | 76.4491 | 0.2200 | 10.0000 |
| seq-3-2-1 | engine | 0.0000 | combined | gated | 0.4100 | 121.6348 | 143.4825 | 108.6164 | 0.0000 | 10.0000 |
