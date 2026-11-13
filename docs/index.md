# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](https://ohara-lab-su.github.io/cap_inspector/en/index.html) [![日本語](https://img.shields.io/badge/lang-ja-blue)](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

A Python package for inspecting bottle-cap opening states using contour geometry, tilt and bottom-edge position, with explicit numerical lift tolerances. Its purpose is stable, reproducible inspection with fewer failures under varying illumination—not merely changing cap color. The project considers both red and black caps; the current color-segmentation implementation is configured for red caps.

## Documentation structure

- **User guide:** camera setup, detection algorithm, acceptance criteria and configuration.
- **API guide:** responsibilities and usage of inspection, status, imaging, parameters and gRPC.
- **Examples:** local and remote inspection, GUI and JSON settings.
- **Generated Python API:** class and method reference generated from source docstrings.

```{toctree}
:maxdepth: 2
:caption: Contents

guide
api_guide
examples
api/modules
```
