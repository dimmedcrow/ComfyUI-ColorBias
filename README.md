
# ComfyUI Color Bias


`Color Bias` is a custom ComfyUI node that does two things at once:

1. Adds color-focused text conditioning to an existing `CONDITIONING` input.
2. Builds a palette-based `LATENT` that can be sent to `KSampler`.

The node is designed to steer color without requiring a separate image reference node.
For models such as Anima, SD15, or SDXL (and variants of it - illustrious, noobai) that have a strong connection between color conditioning and the latent space, this can be a powerful way to achieve more vibrant and accurate colors in your generations.

## Node

**Display name:** `Color Bias`

**Outputs:**

- `conditioning`: the original conditioning plus additional color conditioning.
- `latent`: a generated palette latent adapted to the connected model's latent format.

## Required Inputs

### `conditioning`
Base positive or negative conditioning that you want to modify.

### `model`

### `clip`

### `vae`

### `bypass`
Boolean switch.

- `False`: normal behavior.
- `True`: skips all color processing, returns the original conditioning unchanged, and returns a neutral non-colored latent.

### `active colors`
How many color slots are active.

Valid range: `1` to `5`.

Only the first `N` color inputs are used.

### `global influence`
Overall strength of the added color conditioning.

- Lower values: weaker color push.
- Higher values: stronger color push.
- `0.0`: keeps the original conditioning unchanged, but the node still returns the generated latent.
- `0.5`: the default value, provides a nice balance in most cases.

### `batch size`
How many palette samples to generate in one batch.

This affects the size of the returned latent batch.

### `width`
Width of the generated palette image before VAE encoding.

Higher values increase cost and memory use.

### `height`
Height of the generated palette image before VAE encoding.

Higher values increase cost and memory use.

### `latent`
Palette generation mode if you need extra color conditioning.

Available modes:

- `noise`: creates a noisy palette made from the selected colors.
- `vertical`: creates vertical color bands. (experimental, may be less efficient than `noise`)
- `horizontal`: creates horizontal color bands. (experimental, may be less efficient than `noise`)

### `color 1,2,3,4,5`
Color in hex form from the ComfyUI color picker.

### `strength 1,2,3,4,5`
Relative weight of each color.

This affects both:

- how strongly the color contributes to the generated palette latent,
- how strongly the color contributes to the added color conditioning.

## Output Details

### `conditioning`
Returns a `CONDITIONING` object built from:

- the original input conditioning,
- one additional color-conditioning entry per active color.

Each added entry is generated from a color description derived from the hex value. The node tries to use `webcolors` first for exact named colors and falls back to hue-based naming if no exact CSS-style name is available.

### `latent`
Returns a `LATENT` dictionary with encoded samples.

The latent is generated from a synthetic palette image and then adapted to the connected model's latent format. This is useful for models with non-standard latent channel counts.

If `bypass=True`, the returned latent is neutral gray rather than colorized.

## Typical Workflow

1. Connect your positive conditioning into `conditioning`.
2. Connect the same `model`, `clip`, and `vae` that you use in the rest of your workflow.
3. Pick 1 to 5 colors.
4. Adjust `strength` values to control the palette balance.
5. Send the node's `conditioning` output into the `positive` input of `KSampler`.
6. Send the node's `latent` output into the `latent_image` input of `KSampler`.

## Performance Notes

- Large `width` and `height` values make the node slower.
- Larger `batch size` increases memory use and processing time.
- More active colors means more CLIP conditioning work.
- `noise` mode is heavier than simple banded layouts, even with optimization.

## Installation

Git clone this repository to ComfyUI custom_nodes folder, then restart ComfyUI.

This node depends on:

- `webcolors`
