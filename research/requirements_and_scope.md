# Requirements and research scope / 要求与研究边界

Date: 2026-10-02 (Asia/Shanghai).

## Source of requirements

The user's message names `READMD.md`; the supplied file is `README.md`. The original file, competition screenshot and Chinese review are preserved unchanged.

The user confirmed the default approach: an English manuscript in a general IEEE-style layout, a complete Chinese translation, author details to be supplied, and a clear distinction between public recordings and simulated data. No conference-specific template was supplied.

**Scope clarification:** The final manuscript is an independent thematic study, not a competition submission report or a response to the requester. The material transcribed below records the origin of the topic only. Its numerical thresholds, platform and workflow are not mandatory constraints on this research. References are cited in ordinary scholarly form, without describing them as supplied by a user. Requirement mapping and delivery notes remain outside both manuscript bodies.

## Publication requirements

| Supplied requirement | Implementation and verification |
|---|---|
| English submission | The English manuscript is the primary version; the Chinese manuscript is a reading translation. |
| At least four pages including equations and figures | Verify the generated English PDF page count. |
| Original, unpublished, relevant and technically supported | Write original prose, derive and implement the study, use measured program outputs, cite prior methods, and make no priority claim for established components. Publication history remains the author's responsibility. |
| Similarity at most 24%, any single source at most 3% | These are required external checks. No iThenticate account/report was supplied; neither percentage can be certified from local checks. |
| Technical depth, practical value, innovation and readability | Develop an improved algorithm, compare explicit baselines and ablations, include detection false alarms and unconditional bearing error, and state remaining failure cases. |

## Competition facts transcribed from the supplied image

- The intended platform is a stationary ground acoustic imaging array in an open or partly open outdoor environment.
- The example target is a small consumer multirotor in the DJI Air 3s class; hovering and slow horizontal flight are named.
- The preliminary stage uses organizer-provided array parameters and labelled audio. Test data are not public. These attachments are not present in this workspace.
- Output includes azimuth, elevation and acoustic-map peak position. Azimuth increases counterclockwise from the marked zero direction, in 0–360 degrees. Elevation is the angle above the array plane, in 0–90 degrees.
- At the specified 100 m validation condition, the stated detection accuracy must exceed 80% and the average angular error must not exceed 10 degrees. The exact official accuracy and combined-angle scoring implementation must be obtained from the organizer; the paper must not silently substitute its own metric for that score.
- Processing output must reach at least 5 frames per second. Final-stage real-time scores use thresholds of 5, 8 and 10 frames per second, and separate mean processing-time bands.
- Maximum effective range is defined under the specified conditions by at least 80% detections during a continuous 5 s interval and no detection interruption longer than 0.5 s.
- Device deployment uses Python or C/C++ and depends on the organizer's SDK, geometry, array calibration and interface documents.

## Evidence available and unavailable

Available: one competition screenshot, one 15-page Chinese review, and publication instructions. Public literature can establish prior art; program executions can establish performance under a declared simulation distribution.

Unavailable: official multichannel training/validation/test recordings, official geometry, array response and synchronization calibration, calibrated source levels, meteorological measurements, device SDK and device runtime measurements. Therefore no simulated SNR may be called a measured 100 m, 200 m or 300 m condition. No workstation benchmark may be called organizer-device certification.

The manuscript is an experimental simulation study of a reproducible joint pipeline. It is not an empirical report of the organizer's benchmark, a range demonstration, a real aircraft trial, or a claim to solve drone identity from arbitrary harmonic sound. Any public recordings collected during research are kept separate from the synthetic experiment and must be explicitly identified if actually evaluated.

## Method selection

The current paper develops source-conditioned candidate ranking (SCCR): complementary SRP maps retain competing directions; ordinary and stabilized interference-suppressed beam spectra describe each candidate; a supervised Gaussian-basis regressor selects the target-associated bearing. A separate amplitude-invariant spectral-spatial kernel-ridge detector is trained with single- and multiple-source negatives.

The earlier controlled-weighting experiment is retained as development evidence and archived as `paper/controlled_evaluation_v1.zip`. It is not the final contribution or independent evaluation of the learned methods. The final research objective is a better detection/localization algorithm with measured baseline and ablation comparisons. The fresh evaluation freezes all fitted models and sources, uses separate calibration observations, and tests 1000 positive plus 2000 negative static trials and 24 continuous sequences. The manuscript reports improvement alongside residual tail errors and multi-source false alarms. No claim is made to solve the original physical-range benchmark.

## Possible external validation and submission preparation

1. Replace the illustrative array with the measured geometry and channel ordering; verify yaw zero, handedness, elevation plane and timing offsets with a known source.
2. Split independently acquired field recordings by flight/session, never by neighboring overlapping frames. Set thresholds on a separate validation partition and freeze them before test evaluation.
3. Evaluate detection and bearing at declared physical ranges, reporting all negative recordings and interrupted tracks. No particular competition distance or score is required for the present study.
4. Benchmark an actual device including acquisition, windowing, buffering, output and visualization. State a scientifically justified continuity definition before a field experiment.
5. Add actual author/affiliation information, apply the conference's own template, obtain the required similarity report, and disclose AI assistance if the venue requires it.
