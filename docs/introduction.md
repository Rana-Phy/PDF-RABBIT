# Introduction

## Purpose

PDF-RABBIT is designed to analyze changes in local structural features from
high-throughput X-ray total scattering measurements collected under external
stimuli such as time, temperature, pressure, and chemical or electrochemical
environments.

- The framework extracts reliable and reproducible `S(Q)` and `G(r)` functions
  by optimizing hyperparameters subject to physically meaningful boundary
  conditions.
- It provides an end-to-end workflow covering data reduction, correction,
  optimization, and structural modeling, particularly for large datasets.

## Features

- **Data preprocessing**
- **Intensity corrections**
  - Paalman–Pings absorption correction (cylindrical and flat-plate geometries)
  - Secondary scattering correction
  - Polarization correction
  - Fluorescence correction
  - Breit–Dirac recoil correction
  - Normalization
- **`S(Q)`, `F(Q)`, and `G(r)` optimization** via multi-parameter least-squares
- **`G(r)` ↔ `S(Q)` reverse transformation**
- **Small-box fitting and refinement**

<!-- Add more detail here: motivation, what problem it solves, who it's for. -->
