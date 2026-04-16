import colorsys
import math

import comfy.utils

try:
    import webcolors
except ImportError:
    webcolors = None

class CLIPColorBiasMixer:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "conditioning": ("CONDITIONING",),
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "bypass": ("BOOLEAN", {"default": False}),
                "active colors": ("INT", {"default": 2, "min": 1, "max": 5, "step": 1}),
                "global influence": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "batch size": ("INT", {"default": 1, "min": 1, "max": 64, "step": 1}),
                "width": ("INT", {"default": 1024, "min": 64, "max": 20000, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 20000, "step": 8}),
                "latent": (["noise", "vertical", "horizontal"], {"default": "noise"}),
                "color 1": ("COLOR", {"default": "#FF0000"}),
                "strength 1": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01}),
                "color 2": ("COLOR", {"default": "#00FF00"}),
                "strength 2": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01}),
            },
            "optional": {
                "color 3": ("COLOR", {"default": "#0000FF"}),
                "strength 3": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01}),
                "color 4": ("COLOR", {"default": "#FFFF00"}),
                "strength 4": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01}),
                "color 5": ("COLOR", {"default": "#FF00FF"}),
                "strength 5": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "LATENT")
    RETURN_NAMES = ("conditioning", "latent")
    FUNCTION = "apply_color_bias"
    CATEGORY = "conditioning/colors"

    def get_cached_color_conditioning(self, clip, prompt):
        cache = getattr(self, "_color_conditioning_cache", None)
        if cache is None:
            cache = {}
            self._color_conditioning_cache = cache

        cache_key = (id(clip), prompt)
        cached_conditioning = cache.get(cache_key)
        if cached_conditioning is not None:
            return cached_conditioning

        tokens = clip.tokenize(prompt)
        cached_conditioning = clip.encode_from_tokens_scheduled(tokens)

        if len(cache) >= 128:
            cache.pop(next(iter(cache)))

        cache[cache_key] = cached_conditioning
        return cached_conditioning

    def get_input_value(self, kwargs, *names, default=None):
        for name in names:
            if name in kwargs:
                return kwargs[name]
        return default

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return r, g, b

    def color_metrics(self, hex_color):
        r, g, b = self.hex_to_rgb(hex_color)
        hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
        return {
            "hex": f"#{hex_color.lstrip('#').upper()}",
            "rgb": (round(r * 255), round(g * 255), round(b * 255)),
            "hue": round(hue * 360),
            "saturation": round(saturation * 100),
            "lightness": round(lightness * 100),
        }

    def describe_color(self, hex_color):
        r, g, b = self.hex_to_rgb(hex_color)
        hue, saturation, value = colorsys.rgb_to_hsv(r, g, b)
        hue_degrees = hue * 360.0
        normalized_hex = f"#{hex_color.lstrip('#').upper()}"

        if saturation < 0.12:
            if value < 0.18:
                return "deep black"
            if value > 0.9:
                return "clean white"
            return "neutral gray"

        if webcolors is not None:
            try:
                return webcolors.hex_to_name(normalized_hex)
            except ValueError:
                pass

        if hue_degrees < 8 or hue_degrees >= 352:
            base_color = "red"
        elif hue_degrees < 18:
            base_color = "scarlet"
        elif hue_degrees < 28:
            base_color = "vermilion"
        elif hue_degrees < 38:
            base_color = "orange"
        elif hue_degrees < 48:
            base_color = "amber"
        elif hue_degrees < 58:
            base_color = "golden yellow"
        elif hue_degrees < 68:
            base_color = "yellow"
        elif hue_degrees < 78:
            base_color = "yellow green"
        elif hue_degrees < 88:
            base_color = "chartreuse"
        elif hue_degrees < 100:
            base_color = "lime green"
        elif hue_degrees < 115:
            base_color = "spring green"
        elif hue_degrees < 130:
            base_color = "leaf green"
        elif hue_degrees < 145:
            base_color = "green"
        elif hue_degrees < 160:
            base_color = "emerald"
        elif hue_degrees < 172:
            base_color = "sea green"
        elif hue_degrees < 184:
            base_color = "teal"
        elif hue_degrees < 196:
            base_color = "turquoise"
        elif hue_degrees < 208:
            base_color = "aqua"
        elif hue_degrees < 220:
            base_color = "cyan"
        elif hue_degrees < 232:
            base_color = "sky blue"
        elif hue_degrees < 244:
            base_color = "azure"
        elif hue_degrees < 256:
            base_color = "blue"
        elif hue_degrees < 268:
            base_color = "cobalt blue"
        elif hue_degrees < 280:
            base_color = "indigo"
        elif hue_degrees < 292:
            base_color = "violet"
        elif hue_degrees < 304:
            base_color = "purple"
        elif hue_degrees < 316:
            base_color = "fuchsia"
        elif hue_degrees < 328:
            base_color = "magenta"
        elif hue_degrees < 340:
            base_color = "hot pink"
        elif hue_degrees < 352:
            base_color = "rose"
        else:
            base_color = "pink"

        adjectives = []
        if value < 0.3:
            adjectives.append("deep")
        elif value > 0.85:
            adjectives.append("bright")

        if saturation > 0.75:
            adjectives.append("vivid")
        elif saturation < 0.35:
            adjectives.append("muted")

        return " ".join(adjectives + [base_color])

    def build_color_prompt(self, description, metrics, rgb):
        return (
            f"({description} color palette:1.2), "
            f"({description} tones:1.1), "
            f"subtle {description} lighting, {description} accents, "
            f"hex color {metrics['hex']}, "
            f"RGB {rgb[0]} {rgb[1]} {rgb[2]}, "
            f"HSL hue {metrics['hue']} degrees saturation {metrics['saturation']} percent lightness {metrics['lightness']} percent"
        )

    def build_color_entries(self, active_colors, **kwargs):
        color_entries = []
        for i in range(1, active_colors + 1):
            color_hex = self.get_input_value(kwargs, f"color {i}", f"color_{i}")
            strength = float(self.get_input_value(kwargs, f"strength {i}", f"strength_{i}", default=1.0))
            if not color_hex or strength <= 0:
                continue

            description = self.describe_color(color_hex)
            metrics = self.color_metrics(color_hex)
            rgb = metrics["rgb"]
            prompt = self.build_color_prompt(description, metrics, rgb)
            color_entries.append({
                "hex": metrics["hex"],
                "description": description,
                "prompt": prompt,
                "strength": strength,
                "rgb": rgb,
                "hue": metrics["hue"],
            })

        return color_entries

    def apply_conditioning_strength(self, conditioning, strength):
        scaled_conditioning = []
        for cond_tensor, metadata in conditioning:
            scaled_metadata = metadata.copy()
            scaled_metadata["strength"] = scaled_metadata.get("strength", 1.0) * strength
            scaled_conditioning.append([cond_tensor, scaled_metadata])
        return scaled_conditioning

    def build_palette_summary(self, color_entries):
        return ", ".join(
            f"{entry['hex']} {entry['description']}={entry['strength']:.2f}" for entry in color_entries
        )

    def render_neutral_palette(self, batch_size, width, height):
        torch = __import__("torch")
        return torch.full((batch_size, height, width, 3), 0.5, dtype=torch.float32)

    def render_noise_palette(self, color_tensor, color_probs, batch_size, width, height):
        torch = __import__("torch")

        cell_size = 16 if max(width, height) >= 512 else 8
        noise_height = max(1, (height + cell_size - 1) // cell_size)
        noise_width = max(1, (width + cell_size - 1) // cell_size)

        flat_indices = torch.multinomial(color_probs, batch_size * noise_height * noise_width, replacement=True)
        low_res_noise = color_tensor[flat_indices].view(batch_size, noise_height, noise_width, 3)
        upscaled_noise = torch.nn.functional.interpolate(
            low_res_noise.permute(0, 3, 1, 2),
            size=(height, width),
            mode="nearest",
        )
        return upscaled_noise.permute(0, 2, 3, 1).contiguous()

    def render_palette(self, color_entries, batch_size, width, height, layout):
        torch = __import__("torch")

        total_strength = sum(entry["strength"] for entry in color_entries)
        color_tensor = torch.tensor([self.hex_to_rgb(entry["hex"]) for entry in color_entries], dtype=torch.float32)
        color_weights = torch.tensor([entry["strength"] for entry in color_entries], dtype=torch.float32)
        color_probs = color_weights / total_strength

        if layout == "noise":
            return self.render_noise_palette(color_tensor, color_probs, batch_size, width, height)

        image = torch.zeros((batch_size, height, width, 3), dtype=torch.float32)
        axis_size = width if layout == "vertical" else height
        cumulative_strength = 0.0

        for index, entry in enumerate(color_entries):
            stripe_color = torch.tensor(self.hex_to_rgb(entry["hex"]), dtype=torch.float32)
            start = round(axis_size * cumulative_strength / total_strength)
            cumulative_strength += entry["strength"]

            if index == len(color_entries) - 1:
                end = axis_size
            else:
                end = round(axis_size * cumulative_strength / total_strength)
                end = max(start + 1, min(end, axis_size))

            if layout == "vertical":
                image[:, :, start:end, :] = stripe_color
            else:
                image[:, start:end, :, :] = stripe_color

        return image

    def encode_palette_latent(self, vae, palette_image):
        downscale_ratio = vae.spacial_compression_encode()
        target_height = (palette_image.shape[1] // downscale_ratio) * downscale_ratio
        target_width = (palette_image.shape[2] // downscale_ratio) * downscale_ratio

        if target_height == 0 or target_width == 0:
            raise RuntimeError("Palette size is too small for the selected VAE.")

        pixels = palette_image
        if palette_image.shape[1] != target_height or palette_image.shape[2] != target_width:
            height_offset = (palette_image.shape[1] - target_height) // 2
            width_offset = (palette_image.shape[2] - target_width) // 2
            pixels = palette_image[:, height_offset:height_offset + target_height, width_offset:width_offset + target_width, :]

        return {"samples": vae.encode(pixels), "downscale_ratio_spacial": downscale_ratio}

    def adapt_latent_to_model(self, latent, model):
        if model is None:
            return latent

        latent_format = model.get_model_object("latent_format")
        samples = latent["samples"]
        original_channels = samples.shape[1]

        if latent_format.latent_dimensions == 3 and samples.ndim == 4:
            samples = samples.unsqueeze(2)
        elif latent_format.latent_dimensions == 2 and samples.ndim == 5 and samples.shape[2] == 1:
            samples = samples.squeeze(2)

        if samples.shape[1] != latent_format.latent_channels:
            repeat_factor = math.ceil(latent_format.latent_channels / samples.shape[1])
            repeats = [1] * samples.ndim
            repeats[1] = repeat_factor
            samples = samples.repeat(*repeats)
            samples = samples[:, :latent_format.latent_channels, ...]

        source_ratio = latent.get("downscale_ratio_spacial")
        target_ratio = getattr(latent_format, "spacial_downscale_ratio", None)
        if source_ratio is not None and target_ratio is not None and source_ratio != target_ratio:
            ratio = source_ratio / target_ratio
            if samples.ndim == 4:
                samples = comfy.utils.common_upscale(
                    samples,
                    round(samples.shape[-1] * ratio),
                    round(samples.shape[-2] * ratio),
                    "nearest-exact",
                    crop="disabled",
                )
            elif samples.ndim == 5:
                batch, channels, frames, height, width = samples.shape
                reshaped = samples.permute(0, 2, 1, 3, 4).reshape(batch * frames, channels, height, width)
                reshaped = comfy.utils.common_upscale(
                    reshaped,
                    round(width * ratio),
                    round(height * ratio),
                    "nearest-exact",
                    crop="disabled",
                )
                samples = reshaped.reshape(batch, frames, channels, reshaped.shape[-2], reshaped.shape[-1]).permute(0, 2, 1, 3, 4)

        adapted_latent = latent.copy()
        adapted_latent["samples"] = samples
        adapted_latent["downscale_ratio_spacial"] = target_ratio

        if original_channels != samples.shape[1]:
            print(
                f"Adjusted latent channels for model compatibility: {original_channels} -> {samples.shape[1]}"
            )

        return adapted_latent

    def apply_color_bias(self, conditioning, model, clip, vae, **kwargs):
        if clip is None:
            raise RuntimeError("CLIP input is required for semantic color mixing.")
        bypass = bool(self.get_input_value(kwargs, "bypass", default=False))
        active_colors = int(self.get_input_value(kwargs, "active colors", "active_colors", default=2))
        global_influence = float(self.get_input_value(kwargs, "global influence", "global_influence", default=0.2))
        batch_size = int(self.get_input_value(kwargs, "batch size", "batch_size", default=1))
        width = int(self.get_input_value(kwargs, "width", default=512))
        height = int(self.get_input_value(kwargs, "height", default=512))
        layout = self.get_input_value(kwargs, "latent", "layout", default="noise")

        if bypass:
            neutral_palette = self.render_neutral_palette(batch_size, width, height)
            latent = self.encode_palette_latent(vae, neutral_palette)
            latent = self.adapt_latent_to_model(latent, model)
            print(
                f"Color conditioning bypassed: batch={batch_size}, {width}x{height}, neutral latent returned"
            )
            return (conditioning, latent)

        color_entries = self.build_color_entries(active_colors, **kwargs)
        if not color_entries:
            raise RuntimeError("At least one active color with strength > 0 is required.")

        palette_image = self.render_palette(color_entries, batch_size, width, height, layout)
        latent = self.encode_palette_latent(vae, palette_image)
        latent = self.adapt_latent_to_model(latent, model)

        if global_influence <= 0:
            return (conditioning, latent)

        total_color_strength = sum(entry["strength"] for entry in color_entries)
        effective_influence = float(global_influence) ** 0.65
        mixed_conditioning = list(conditioning)

        for entry in color_entries:
            relative_strength = entry["strength"] / total_color_strength
            conditioning_strength = effective_influence * relative_strength
            color_conditioning = self.get_cached_color_conditioning(clip, entry["prompt"])
            mixed_conditioning.extend(self.apply_conditioning_strength(color_conditioning, conditioning_strength))

        print(
            f"Color conditioning applied: {active_colors} color(s), influence={global_influence:.2f}, batch={batch_size}, {width}x{height}, layout={layout}, palette={self.build_palette_summary(color_entries)}"
        )
        return (mixed_conditioning, latent)

NODE_CLASS_MAPPINGS = {
    "CLIPColorBiasMixer": CLIPColorBiasMixer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CLIPColorBiasMixer": "Color Bias",
}

