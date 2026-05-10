"""Unit conversion and derived-variable helpers.

All functions expect *xarray* data (DataArray / Dataset) that come straight
from the CLM history files so we can slice along ``levsoi`` using
xarray indexing.

The soil-moisture helpers support both integer and list-based levsoi mappings:

    LEVSOI_MAP = {
        "default": {
            "sm_5cm":  1,
            "sm_20cm": 3,
            "sm_50cm": 6,
        }
    }

or

    LEVSOI_MAP = {
        "default": {
            "sm_5cm":  [1],
            "sm_20cm": [3, 4],
            "sm_50cm": [5, 6],
        }
    }

If a mapping value is a list/tuple with multiple entries, the selected CLM
layers are averaged before any SMR weighting is applied.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import xarray as xr

from ..config import LEVSOI_MAP, SMR_LAYER_WEIGHTS, VARIABLES


# ---------------------------------------------------------------------------
# Soil-layer lookup
# ---------------------------------------------------------------------------
LevsoiSpec = int | Sequence[int]


def levsoi_indices_for_site(site: str) -> dict[str, LevsoiSpec]:
    """Return the soil-layer mapping for ``site``.

    Values may be either integers, e.g. ``3``, or lists/tuples of integers,
    e.g., ``[3, 4]``.  The latter means the layers should be averaged.
    """
    return LEVSOI_MAP.get(site, LEVSOI_MAP["default"])


def _normalise_levsoi_spec(spec: LevsoiSpec) -> list[int]:
    """Convert an integer or sequence of integers to a clean list of ints."""
    if isinstance(spec, (int, np.integer)):
        return [int(spec)]

    if isinstance(spec, Sequence) and not isinstance(spec, (str, bytes)):
        if len(spec) == 0:
            raise ValueError("levsoi index list cannot be empty")
        return [int(idx) for idx in spec]

    raise TypeError(
        "levsoi index must be an int or a sequence of ints; "
        f"got {type(spec).__name__}: {spec!r}"
    )


def _select_layer_or_average(da: xr.DataArray, spec: LevsoiSpec) -> xr.DataArray:
    """Select one levsoi layer or average several levsoi layers.

    Parameters
    ----------
    da
        CLM variable with a ``levsoi`` dimension.
    spec
        Either an integer index, such as ``3``, or a list/tuple of indices,
        such as ``[3, 4]``.

    Returns
    -------
    DataArray
        The selected layer, or the mean across selected layers.  The returned
        array has no ``levsoi`` dimension.
    """
    if "levsoi" not in da.dims:
        raise ValueError("Expected DataArray with a 'levsoi' dimension")

    indices = _normalise_levsoi_spec(spec)
    selected = da.isel(levsoi=indices)

    if len(indices) == 1:
        return selected.squeeze("levsoi", drop=True)

    return selected.mean(dim="levsoi")


def _format_levsoi_spec(spec: LevsoiSpec) -> str:
    """Human-readable representation for metadata."""
    indices = _normalise_levsoi_spec(spec)
    if len(indices) == 1:
        return str(indices[0])
    return "[" + ", ".join(str(i) for i in indices) + "]"


# ---------------------------------------------------------------------------
# Derived variables
# ---------------------------------------------------------------------------
def surface_soil_moisture(
    da: xr.DataArray,
    site: str,
    scale: float = 100.0,
) -> xr.DataArray:
    """Extract/average the configured 5 cm H2OSOI layer(s) and convert to %.

    If ``LEVSOI_MAP[site]["sm_5cm"]`` is an integer, one layer is selected.
    If it is a list/tuple, those layers are averaged.
    """
    idxs = levsoi_indices_for_site(site)
    spec = idxs["sm_5cm"]

    surface = _select_layer_or_average(da, spec) * scale
    surface.attrs["units"] = "%"
    surface.attrs["derived_from"] = (
        f"H2OSOI using levsoi={_format_levsoi_spec(spec)}"
    )
    return surface


def root_zone_soil_moisture(
    da: xr.DataArray,
    site: str,
    scale: float = 100.0,
    weights: dict[str, float] | None = None,
) -> xr.DataArray:
    """Weighted mean of H2OSOI across configured 5/20/50 cm layers.

    Each configured depth may be one integer layer or a list/tuple of layers.
    For list/tuple mappings, the selected layers are averaged first, then the
    5/20/50 cm values are combined using ``SMR_LAYER_WEIGHTS``.

    this function computes

        SMR = (
            w5  * H2OSOI[1]
          + w20 * H2OSOI[3]
          + w50 * H2OSOI[6]
        ) / sum(weights) * 100
    """
    idxs = levsoi_indices_for_site(site)
    w = weights or SMR_LAYER_WEIGHTS

    required = ("sm_5cm", "sm_20cm", "sm_50cm")
    missing_from_map = [key for key in required if key not in idxs]
    if missing_from_map:
        raise KeyError(
            f"Missing levsoi mapping keys for site {site}: {missing_from_map}"
        )

    missing_from_weights = [key for key in required if key not in w]
    if missing_from_weights:
        raise KeyError(
            f"Missing SMR weight keys for site {site}: {missing_from_weights}"
        )

    total_weight = sum(float(w[key]) for key in required)
    if total_weight <= 0:
        raise ValueError(f"SMR weights must sum to a positive value, got {total_weight}")

    sm_5 = _select_layer_or_average(da, idxs["sm_5cm"])
    sm_20 = _select_layer_or_average(da, idxs["sm_20cm"])
    sm_50 = _select_layer_or_average(da, idxs["sm_50cm"])

    root = (
        sm_5 * float(w["sm_5cm"])
        + sm_20 * float(w["sm_20cm"])
        + sm_50 * float(w["sm_50cm"])
    ) / total_weight * scale

    root.attrs["units"] = "%"
    root.attrs["derived_from"] = (
        "weighted mean of H2OSOI using levsoi groups "
        f"5cm={_format_levsoi_spec(idxs['sm_5cm'])}, "
        f"20cm={_format_levsoi_spec(idxs['sm_20cm'])}, "
        f"50cm={_format_levsoi_spec(idxs['sm_50cm'])}; "
        f"weights={w}"
    )
    return root


def apply_unit_scale(da: xr.DataArray, variable: str) -> xr.DataArray:
    """Multiply ``da`` by ``VARIABLES[variable]['scale']``.

    Used for ET and other variables with non-unity scale factors.  Variables
    with scale=1.0 are returned unchanged.
    """
    scale = VARIABLES[variable]["scale"]
    if scale == 1.0:
        return da

    out = da * scale
    out.attrs.update(da.attrs)
    return out