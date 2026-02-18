"""Translation step: EN→ES using NLLB-200 distilled."""

import gc
from pathlib import Path

import torch

from src.device import get_device
from src.pipeline.base import PipelineStep, console
from src.utils.io import read_json, write_json
from src.utils.text import clean_text, text_hash


class TranslateStep(PipelineStep):
    name = "translate"
    output_files = ["translations.json"]

    def execute(self, **kwargs):
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        cfg = self.config["translation"]
        device = get_device("translation", self.config["devices"].get("translation", "auto"))

        console.print(f"    Model: {cfg['model']}, device: {device}")

        # Load merged segments
        merged_data = read_json(self.workdir / "merged_segments.json")
        segments = merged_data["segments"]

        # Load translation cache if exists
        cache_path = self.workdir / ".translation_cache.json"
        cache = {}
        if cache_path.exists():
            try:
                cache = read_json(cache_path)
            except Exception:
                cache = {}

        # Load model
        console.print("    Loading NLLB-200 model...")
        tokenizer = AutoTokenizer.from_pretrained(cfg["model"])
        model = AutoModelForSeq2SeqLM.from_pretrained(cfg["model"]).to(device)
        model.eval()

        # Set source language
        tokenizer.src_lang = cfg.get("src_lang", "eng_Latn")
        tgt_lang = cfg.get("tgt_lang", "spa_Latn")
        forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)

        # Translate each segment
        translated_segments = []
        total = len(segments)

        for i, seg in enumerate(segments):
            text_en = clean_text(seg["text_en"])
            t_hash = text_hash(text_en)

            # Check cache
            if t_hash in cache:
                text_es = cache[t_hash]
                console.print(f"    [{i+1}/{total}] (cached) {text_en[:50]}...")
            else:
                try:
                    text_es = self._translate_text(
                        text_en, tokenizer, model, device,
                        forced_bos_token_id, cfg.get("max_length", 512),
                    )
                    cache[t_hash] = text_es
                    console.print(f"    [{i+1}/{total}] {text_en[:40]}... → {text_es[:40]}...")
                except Exception as e:
                    console.print(f"    [{i+1}/{total}] [red]Translation failed, keeping EN[/red]: {e}")
                    text_es = text_en

            translated_segments.append({
                **seg,
                "text_es": text_es,
            })

        # Save results
        write_json({"segments": translated_segments}, self.workdir / "translations.json")

        # Save cache
        write_json(cache, cache_path)

        # Free memory
        del model, tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        console.print(f"    Translated {total} segments → translations.json")

    @staticmethod
    def _translate_text(
        text: str,
        tokenizer,
        model,
        device: torch.device,
        forced_bos_token_id: int,
        max_length: int,
    ) -> str:
        """Translate a single text string EN→ES."""
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            generated = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=max_length,
            )

        return tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
