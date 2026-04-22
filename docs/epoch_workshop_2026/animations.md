---
file_format: mystnb
kernelspec:
  name: python3
---

# Animations

```{note}
Unfortunately, these animations are not interactive like the rest of the documentation as building them on readthedocs takes too long so we display the GIFs from the datasets instead.
```

## Animate Density 1D

- **input deck:** <path:datasets/1_1_drifting_bunch/input.deck>
- **Python File:** <path:animating/animate_1D_density.py>

```{literalinclude} ./animating/animate_1D_density.py
```
![datasets/1_1_drifting_bunch/number_density.gif](datasets/1_1_drifting_bunch/number_density.gif)

## Animate Poynting Flux 1D

- **input deck:** <path:datasets/3_3_Gaussian_1d_laser/input.deck>
- **Python File:** <path:animating/animate_1D_poynting_flux.py>

```{literalinclude} ./animating/animate_1D_poynting_flux.py
```
![datasets/3_3_Gaussian_1d_laser/laser.gif](datasets/3_3_Gaussian_1d_laser/laser.gif)

## Animate Distribution Function Multi-Species 2D

- **input deck:** <path:datasets/2_1_two_stream_instability/input.deck>
- **Python File:** <path:animating/animate_2D_dist_fn_multispecies.py>
- **Python File (alternative):** <path:animating/animate_2D_dist_fn_multispecies_alternative.py>

```{literalinclude} ./animating/animate_2D_dist_fn_multispecies.py
```
![datasets/2_1_two_stream_instability/phase_space.gif](datasets/2_1_two_stream_instability/phase_space.gif)

## Animate Poynting Flux 2D

- **input deck:** <path:datasets/3_5_Gaussian_beam/input.deck>
- **Python File:** <path:animating/animate_2D_poynting_flux.py>

```{literalinclude} ./animating/animate_2D_poynting_flux.py
```
![datasets/3_5_Gaussian_beam/laser.gif](datasets/3_5_Gaussian_beam/laser.gif)
